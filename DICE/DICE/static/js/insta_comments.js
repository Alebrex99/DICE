console.log("Instagram comment likes ready!");

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.comment-like-button').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var countSpan = btn.querySelector('.comment-like-count');
            var count = parseInt(countSpan.textContent) || 0;
            var liked = btn.getAttribute('data-liked') === 'true';

            if (!liked) {
                btn.setAttribute('data-liked', 'true');
                countSpan.textContent = (count + 1).toString();
            } else {
                btn.setAttribute('data-liked', 'false');
                countSpan.textContent = (count - 1).toString();
            }
            // Does NOT change heart colour — red is reserved for author-liked comments (render-time).
        });
    });
});