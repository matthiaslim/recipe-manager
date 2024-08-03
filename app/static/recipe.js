document.addEventListener('DOMContentLoaded', function () {
    loadPreviousSearches();

    function saveSearchTerm(term) {
        fetch('/save_search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ term: term })
        }).then(() => loadPreviousSearches());
    }

    function loadPreviousSearches() {
        fetch('/load_searches')
            .then(response => response.json())
            .then(searches => {
                const datalist = document.getElementById('previousSearches');
                datalist.innerHTML = '';
                searches.forEach(search => {
                    const option = document.createElement('option');
                    option.value = search;
                    datalist.appendChild(option);
                });
            });
    }

    // Save search term on form submission
    document.getElementById('searchForm').addEventListener('submit', function (event) {
        const searchTerm = document.getElementById('searchRecipes').value;
        saveSearchTerm(searchTerm);
    });
});