# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from .trace import Trace


class Client:
    def __init__(self, trace: Trace = None) -> None:
        self.trace = trace

    def run(self, pre_prompt: str, prompt: str, completion_config: dict = {}) -> str:
        self.trace_query(pre_prompt, prompt, completion_config)

    def run_messages(
        self,
        messages: list[dict],
        trace_input_messages: bool = True,
        completion_config: dict = {},
    ) -> list[dict]:
        if trace_input_messages:
            self.trace.write_separator()
            for message in messages:
                self.trace_message(message)

    def trace_message(self, message: dict) -> str:
        if self.trace is not None:
            self.trace(f"<<{message['role']}>>")
            self.trace(message["content"])

    def trace_query(
        self, pre_prompt: str, prompt: str, completion_config: dict = {}
    ) -> str:
        if self.trace is not None:
            self.trace.write_separator()
            self.trace("<<PRE-PROMPT>>")
            self.trace(pre_prompt)
            self.trace("<<PROMPT>>")
            self.trace(prompt)

    def trace_response(self, response: str) -> str:
        if self.trace is not None:
            self.trace("<<RESPONSE>>")
            self.trace(response)


class HuggingFaceClient(Client):
    def __init__(
        self,
        model: str = None,
        pipeline_configuration: dict = {},
        seed: int = 42,
        api_key: str | None = None,
        trace: Trace = None,
    ) -> None:
        super().__init__(trace=trace)

        # to decrease the chance of hard-to-track bugs, we don't allow the 'model' key in pipeline_configuration
        if "model" in pipeline_configuration:
            raise ValueError(
                "The 'model' key is not allowed in pipeline_configuration. Use the 'model' parameter instead."
            )

        # data members
        self.model = model
        self.seed = seed
        if api_key is None:
            import os

            self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.api_key = api_key

        # complete pipeline config
        from transformers import pipeline

        default_configuration = {
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "device": "cuda:0",
            "max_new_tokens": 1024,
        }
        merged_configuration = {**default_configuration, **pipeline_configuration}

        # model
        if self.model is not None:
            merged_configuration["model"] = self.model

        # seed
        from transformers import set_seed

        set_seed(self.seed)

        # tokenizer and pipeline for generation
        from transformers import AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(
            default_configuration["model"], api_key=self.api_key
        )
        self.generator = pipeline("text-generation", **merged_configuration)

    def run(self, pre_prompt: str, prompt: str, completion_config: dict = {}) -> str:
        super().run(pre_prompt, prompt, completion_config)
        messages = [
            {"role": "system", "content": pre_prompt},
            {"role": "user", "content": prompt},
        ]

        completion = self.generator(
            messages,
            **completion_config,
            pad_token_id=self.generator.tokenizer.eos_token_id,
        )

        ret = completion[0]["generated_text"][-1]["content"]
        self.trace_response(ret)
        return ret

    def run_messages(
        self, messages, trace_input_messages: bool = True, completion_config={}
    ) -> list[dict]:
        super().run_messages(messages, trace_input_messages, completion_config)
        completion = self.generator(
            messages,
            **completion_config,
            pad_token_id=self.generator.tokenizer.eos_token_id,
        )

        ret = completion[0]["generated_text"]
        self.trace_message(ret[-1])
        return ret


class OpenAIClient(Client):
    def __init__(
        self,
        base_url: str,
        model: str = None,
        seed: int = 42,
        api_key: str | None = None,
        trace: Trace = None,
    ) -> None:
        super().__init__(trace=trace)

        self.base_url = base_url
        self.model = (
            model
            if model is not None
            else "nvdev/nvidia/llama-3.1-nemotron-70b-instruct"
        )
        if api_key is None:
            import os

            api_key = os.getenv("NGC_API_KEY")
        self.api_key = api_key
        self.seed = seed

        from openai import OpenAI

        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def _invoke(self, messages: list[dict], completion_config: dict = {}) -> str:
        default_settings = {
            "model": self.model,
            "top_p": 1,
            "temperature": 0.0,
            "max_tokens": 2048,
            "stream": True,
            "seed": self.seed,
        }

        merged_settings = {**default_settings, **completion_config}
        
        # Clean up messages for Groq compatibility
        cleaned_messages = []
        for message in messages:
            # Skip empty system messages (Groq doesn't accept null/empty content)
            if message["role"] == "system" and (not message.get("content") or message["content"].strip() == ""):
                continue
            # Rename ipython role to function for compatibility
            if message["role"] == "ipython":
                message["role"] = "function"
            cleaned_messages.append(message)
        
        # Ensure we have at least one message
        if not cleaned_messages:
            cleaned_messages = [{"role": "user", "content": "Hello"}]
            
        completion = self.client.chat.completions.create(
            messages=cleaned_messages, **merged_settings
        )

        ret: str = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                ret += chunk.choices[0].delta.content

        return ret

    def run(self, pre_prompt: str, prompt: str, completion_config: dict = {}) -> str:
        super().run(pre_prompt, prompt, completion_config)

        # Build messages, handling empty pre_prompt for Groq compatibility
        messages = []
        if pre_prompt and pre_prompt.strip():
            messages.append({"role": "system", "content": pre_prompt})
        messages.append({"role": "user", "content": prompt})

        ret = self._invoke(
            messages=messages,
            completion_config=completion_config,
        )

        self.trace_response(ret)
        return ret

    def run_messages(
        self, messages, trace_input_messages: bool = True, completion_config={}
    ) -> list[dict]:
        super().run_messages(messages, trace_input_messages, completion_config)

        ret_str: str = self._invoke(
            messages=messages, completion_config=completion_config
        )
        ret_msg: dict = {"role": "assistant", "content": ret_str}

        self.trace_message(ret_msg)
        return [*messages, ret_msg]
