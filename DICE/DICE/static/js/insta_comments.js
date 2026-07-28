console.log("Instagram comment likes ready!");

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.comment-like-button').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var countSpan = btn.querySelector('.comment-like-count');
            var icon = btn.querySelector('.comment-like-icon');
            var count = parseInt(countSpan.textContent) || 0;
            var liked = btn.getAttribute('data-liked') === 'true';

            if (!liked) {
                btn.setAttribute('data-liked', 'true');
                countSpan.textContent = (count + 1).toString();
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill', 'text-danger');    // turn red on like
            } else {
                btn.setAttribute('data-liked', 'false');
                countSpan.textContent = (count - 1).toString();
                icon.classList.remove('bi-heart-fill', 'text-danger'); // back to white
                icon.classList.add('bi-heart');
            }
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