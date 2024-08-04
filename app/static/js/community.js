document.addEventListener('DOMContentLoaded', () => {
    const addCommentForm = document.getElementById('addCommentForm');
    const replyForm = document.getElementById('replyForm');
    const commentsData = document.getElementById('comments-data');
    const replyModal = new bootstrap.Modal(document.getElementById('replyModal'));

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
                            replyInput.value = ''; // Clear input
                            fetchReplies(threadId); // Refresh replies
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

    // Refresh the page when the reply modal is closed
    document.getElementById('replyModal').addEventListener('hidden.bs.modal', () => {
        window.location.reload();
    });

    async function fetchReplies(threadId) {
        try {
            const response = await fetch(`/replies/${threadId}`); // Define this endpoint to get replies
            if (response.ok) {
                const data = await response.json();
                const replyContainer = document.getElementById('replyContainer');
                replyContainer.innerHTML = data.replies.map(reply => `
                    <div class="reply">
                        <p><strong>${reply.user}:</strong> ${reply.reply}</p>
                    </div>
                `).join('');
            } else {
                console.error('Error fetching replies');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
});