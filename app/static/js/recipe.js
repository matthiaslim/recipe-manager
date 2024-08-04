document.addEventListener('DOMContentLoaded', function () {
    loadPreviousSearches();

    function saveSearchTerm(term) {
        fetch('/save_search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({term: term})
        }).then(() => loadPreviousSearches());
    }

    function loadPreviousSearches() {
        fetch('/load_searches')
            .then(response => response.json())
            .then(searches => {
                const previousSearches = document.getElementById('previousSearches');
                const previousSearchesContainer = document.getElementById('previousSearchesContainer');

                if (!Array.isArray(searches)) {
                    console.error('Expected an array of searches but got:', searches);
                    return;
                }

                if (!previousSearchesContainer) {
                    console.error('Element #previousSearchesContainer not found.');
                    return;
                }

                previousSearches.innerHTML = '';

                searches.forEach(search => {
                    const item = document.createElement('li');
                    item.className = 'list-group-item d-flex justify-content-between align-items-center';

                    const textNode = document.createElement('span');
                    textNode.className = 'flex-grow-1';
                    textNode.textContent = search;

                    // Create the remove button
                    const removeButton = document.createElement('button');
                    removeButton.className = 'btn btn-outline-dark';
                    removeButton.innerHTML = '<i class="fas fa-times"></i>';
                    removeButton.addEventListener('click', (event) => {
                        event.stopPropagation(); // Prevent triggering parent click
                        removeSearchTerm(search);
                    });

                    item.appendChild(textNode);
                    item.appendChild(removeButton);
                    previousSearches.appendChild(item);

                    // Add an event listener to set the search term on click (excluding the remove button)
                    item.addEventListener('click', function (event) {
                        // Ensure the event is not triggered by clicking the remove button
                        if (!event.target.closest('.btn-outline-dark')) {
                            document.getElementById('searchRecipes').value = search;
                            new bootstrap.Collapse(previousSearchesContainer, {
                                toggle: false
                            }).hide();
                        }
                    });
                });
            });
    }

    function removeSearchTerm(term) {
        fetch('/remove_search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({term: term})
        }).then(() => loadPreviousSearches());
    }

    // Close the dropdown when clicking outside
    document.addEventListener('click', function (event) {
        const searchInput = document.getElementById('searchRecipes');
        const previousSearchesContainer = document.getElementById('previousSearchesContainer');

        // Check if the previousSearchesContainer is present
        if (previousSearchesContainer && !previousSearchesContainer.contains(event.target) && event.target !== searchInput) {
            new bootstrap.Collapse(previousSearchesContainer, {
                toggle: false
            }).hide();
        }
    });

    // Save search term on form submission
    document.getElementById('searchForm').addEventListener('submit', function (event) {
        const searchTerm = document.getElementById('searchRecipes').value;
        if (searchTerm.trim() === '') {
            event.preventDefault(); // Stop form submission if search term is empty
            return;
        }
        saveSearchTerm(searchTerm);
    });

    // Handle Enter key press within the input field
    document.getElementById('searchRecipes').addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevent the default form submission
            const searchTerm = document.getElementById('searchRecipes').value;
            if (searchTerm.trim() !== '') {
                saveSearchTerm(searchTerm);
                document.getElementById('searchForm').submit(); // Programmatically submit the form
            }
        }
    });
});
