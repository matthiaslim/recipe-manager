document.addEventListener('DOMContentLoaded', () => {
    const addCommentForm = document.getElementById('addCommentForm');
    const replyForm = document.getElementById('replyForm');
    const commentsData = document.getElementById('comments-data');
    const replyModal = new bootstrap.Modal(document.getElementById('replyModal'));

    // Function to calculate time difference
    function timeDifference(current, previous) {
        const msPerMinute = 60 * 1000;
        const msPerHour = msPerMinute * 60;
        const msPerDay = msPerHour * 24;
        const msPerMonth = msPerDay * 30;
        const msPerYear = msPerDay * 365;

        const elapsed = current - previous;

        if (elapsed < msPerMinute) {
            return Math.round(elapsed / 1000) + ' seconds ago';
        } else if (elapsed < msPerHour) {
            return Math.round(elapsed / msPerMinute) + ' min ago';
        } else if (elapsed < msPerDay) {
            return Math.round(elapsed / msPerHour) + ' hr ago';
        } else if (elapsed < msPerMonth) {
            return Math.round(elapsed / msPerDay) + ' days ago';
        } else if (elapsed < msPerYear) {
            return Math.round(elapsed / msPerMonth) + ' mth ago';
        } else {
            return Math.round(elapsed / msPerYear) + ' yr ago';
        }
    }

    // Update the time difference for each comment
    document.querySelectorAll('.card').forEach(card => {
        const createdTime = new Date(card.getAttribute('data-created-time'));
        const currentTime = new Date();
        const timeDiff = timeDifference(currentTime, createdTime);
        card.querySelector('.comment-time').innerText = timeDiff;
    });

    // Handle adding a comment
    addCommentForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const commentTitle = document.getElementById('commentTitleInput');
        const commentInput = document.getElementById('commentInput');
        const commentTitleText = commentTitle.value.trim();
        const commentText = commentInput.value.trim();

        if (commentText) {
            try {
                const response = await fetch('/add_comment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({commentTitle: commentTitleText, comment: commentText})
                });

                if (response.ok) {
                    window.location.reload(); // Reload page to show new comment
                } else {
                    console.error('Error adding comment');
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
    });

    // Handle opening reply modal and setting up reply form
    commentsData.addEventListener('click', (event) => {
        if (event.target.classList.contains('replybutton')) {
            const threadId = event.target.getAttribute('data-thread-id');
            const commentElement = event.target.closest('.card');
            const commentContent = commentElement.querySelector('.comment-text').innerHTML;
            const replyContainer = document.getElementById('replyContainer');
            const commentTitleDiv = document.getElementById('commentTitle');
            const commentContentDiv = document.getElementById('commentContent');

            commentTitleDiv.innerHTML = `<h5>${commentElement.querySelector('.comment-title').innerHTML}</h5>`;
            commentContentDiv.innerHTML = `<p>${commentContent}</p>`;
            replyContainer.innerHTML = ''; // Clear previous replies

            // Fetch and display replies
            fetchReplies(threadId);

            // Set up reply form submission
            replyForm.onsubmit = async (replyEvent) => {
                replyEvent.preventDefault();
                const replyInput = document.getElementById('replyInput');
                const replyText = replyInput.value.trim();

                if (replyText) {
                    try {
                        const response = await fetch('/add_reply', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                comment_index: threadId,
                                reply: replyText
                            })
                        });

                        if (response.ok) {
                            replyInput.value = ''; // Clear reply input
                            fetchReplies(threadId); // Reload replies
                        } else {
                            console.error('Error adding reply');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                    }
                }
            };

            replyModal.show();
        }
    });

    // Fetch replies for a given thread and display them
    async function fetchReplies(threadId) {
        try {
            const response = await fetch(`/replies/${threadId}`);
            if (response.ok) {
                const data = await response.json();
                const replyContainer = document.getElementById('replyContainer');

                if (data.replies) {
                    replyContainer.innerHTML = ''; // Clear existing replies
                    data.replies.forEach(reply => {
                        const replyElement = document.createElement('div');
                        replyElement.className = 'reply card mb-2';
                        replyElement.innerHTML = `
                            <div class="card-body">
                                <h6 class="card-subtitle mb-2 text-muted">${reply.user}</h6>
                                <p class="card-text">${reply.reply}</p>
                                <p class="card-text"><small class="text-muted">${timeDifference(new Date(), new Date(reply.created_time))}</small></p>
                            </div>
                        `;
                        replyContainer.appendChild(replyElement);
                    });
                }
            } else {
                console.error('Error fetching replies');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
});
