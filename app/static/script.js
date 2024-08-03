    document.addEventListener('DOMContentLoaded', (event) => {
        const addFavouritesButton = document.getElementById('addFavourites');

        addFavouritesButton.addEventListener('click', () => {
            // Show the notification
            const notification = document.getElementById('notification');
            notification.style.display = 'block';

            // Hide the notification after 3 seconds
            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);

            // Change button class to btn-danger
            addFavouritesButton.classList.remove('btn-light');
            addFavouritesButton.classList.add('btn-danger');
        });
    });
