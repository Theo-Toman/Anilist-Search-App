
    function addToSearchBox(searchBoxId, valueToAdd) {
        document.getElementById(searchBoxId).value = valueToAdd;
        searchAnime(true);
    }
    function searchStudios() {
        var query = `
            query (
                $page: Int,
                $perPage: Int,
                $search: String
            ) {
                Page (page: $page, perPage: $perPage) {
                    pageInfo {
                        total
                        currentPage
                        lastPage
                        hasNextPage
                        perPage
                    }
                    studios (
                        search: $search
                    ) {
                        id
                        name
                    }
                }
            }
        `;

        // Define our query variables and values that will be used in the query request
        console.log(document.getElementById('studio-option-search').value)
        var variables = {
            page: 1,
            perPage: 15,
            search: document.getElementById('studio-option-search').value
        };

        // Define the config we'll need for our Api request
        var url = 'https://graphql.anilist.co',
        options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                variables: variables
            })
        };

        console.log(fetch(url, options))

        // Make the HTTP Api request
        fetch(url, options).then(handleResponse)
                           .then(handleData)
                           .catch(handleError);

        function handleResponse(response) {
            return response.json().then(function (json) {
                return response.ok ? json : Promise.reject(json);
            });
        }

        function handleData(data) {
            data = data['data']['Page']['studios']
            console.log(data);
            let div = document.getElementsByClassName('search-dropdown-content studio-search')[0];
            div.replaceChildren();

            for (let i = 0; i < data.length; i++) {
                let element = document.createElement('button');

                element.innerHTML = data[i].name;
                element.addEventListener("click", function () {addToSearchBox('studio-option-search', data[i].name)})

                div.appendChild(element);
            }

            if (document.getElementById('studio-option-search').value == "") {
                searchAnime(true);
            }
        }

        function handleError(error) {
            alert('Error, check console');
            console.error(error);
        }
    }
