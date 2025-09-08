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
def perform_search(search_phrase: str):
    """
    Performs a search using the Tavily API and returns a list of search result objects.

    Args:
        search_phrase (str): The phrase to search for using the Tavily API.

    Returns:
        List[Dict[str, Any]]: A list of search result dictionaries obtained from the Tavily API. Each dictionary has 'content' field with text retrieved from the result, and a 'url' field that keeps the url of the search result.

    Raises:
        TavilyClientError: If there is an issue with the Tavily API client or the search request.
        KeyError: If the expected 'results' key is missing in the search response.

    """
    from tavily import TavilyClient
    import os
    
    # Try to get API key from multiple sources
    api_key = None
    
    # Method 1: Try environment variable
    api_key = os.getenv('TAVILY_API_KEY')
    
    # Method 2: Try reading from file in current directory
    if not api_key:
        try:
            with open("tavily_api.txt", "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            pass
    
    # Method 3: Try reading from backend directory
    if not api_key:
        try:
            backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
            api_key_path = os.path.join(backend_path, "tavily_api.txt")
            with open(api_key_path, "r") as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            pass
    
    client = TavilyClient(api_key=api_key)
    search_response = client.search(search_phrase, include_raw_content=True)
    return search_response["results"]
