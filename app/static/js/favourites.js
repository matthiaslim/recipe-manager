document.addEventListener('DOMContentLoaded', function () {
    // Handle search form submission
    document.getElementById('searchForm').addEventListener('submit', function (event) {
        event.preventDefault();
        searchRecipes();
    });

    // Handle pagination link clicks
    document.querySelectorAll('.pagination a').forEach(function (link) {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            fetchPage(this.href);
        });
    });

    // Function to handle dynamic search
    function searchRecipes() {
        const searchForm = document.getElementById('searchForm');
        const formData = new FormData(searchForm);

        fetch(searchForm.action + '?' + new URLSearchParams(formData))
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('#myFavouriteRecipeContainer').innerHTML;
                const newPagination = doc.querySelector('.d-flex').innerHTML;

                document.querySelector('#myFavouriteRecipeContainer').innerHTML = newContent;
                document.querySelector('.d-flex').innerHTML = newPagination;

                // Re-attach event listeners to new pagination links
                document.querySelectorAll('.pagination a').forEach(function (link) {
                    link.addEventListener('click', function (event) {
                        event.preventDefault();
                        fetchPage(this.href);
                    });
                });
            })
            .catch(error => {
                console.error('Error fetching search results:', error);
            });
    }

    // Function to handle pagination link clicks
    function fetchPage(url) {
        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContent = doc.querySelector('#myFavouriteRecipeContainer').innerHTML;
                const newPagination = doc.querySelector('.d-flex').innerHTML;

                document.querySelector('#myFavouriteRecipeContainer').innerHTML = newContent;
                document.querySelector('.d-flex').innerHTML = newPagination;

                // Re-attach event listeners to new pagination links
                document.querySelectorAll('.pagination a').forEach(function (link) {
                    link.addEventListener('click', function (event) {
                        event.preventDefault();
                        fetchPage(this.href);
                    });
                });
            })
            .catch(error => {
                console.error('Error fetching page:', error);
            });
    }
});