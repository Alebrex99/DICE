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

    // "View replies (N)" — expand/collapse threaded replies
    document.querySelectorAll('.view-replies-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var target = document.getElementById(btn.getAttribute('data-target'));
            if (!target) return;
            var isHidden = target.style.display === 'none';
            target.style.display = isHidden ? 'block' : 'none';
            var label = btn.querySelector('.view-replies-label');
            if (label) {
                label.textContent = isHidden
                    ? 'Hide replies'
                    : 'View replies (' + btn.getAttribute('data-count') + ')';
            }
        });
    });

});