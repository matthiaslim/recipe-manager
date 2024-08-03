document.addEventListener('DOMContentLoaded', function () {
    loadPreviousSearches();

    function saveSearchTerm(term) {
        let searches = JSON.parse(localStorage.getItem('previousSearches')) || [];
        searches = searches.filter(search => search !== term);
        searches.unshift(term);
        searches = searches.slice(0, 10);
        localStorage.setItem('previousSearches', JSON.stringify(searches));
        loadPreviousSearches();
    }

    function loadPreviousSearches() {
        const searches = JSON.parse(localStorage.getItem('previousSearches')) || [];
        const datalist = document.getElementById('previousSearches');
        datalist.innerHTML = '';
        searches.forEach(search => {
            const option = document.createElement('option');
            option.value = search;
            datalist.appendChild(option);
        });
    }

    // Save search term on form submission
    document.getElementById('searchForm').addEventListener('submit', function (event) {
        const searchTerm = document.getElementById('searchRecipes').value;
        saveSearchTerm(searchTerm);
    });
});