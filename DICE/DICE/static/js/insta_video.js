document.addEventListener('DOMContentLoaded', function () {
    /* observer: API browser che controlla se gli elementi osservati attraversano
        la soglia di visibilità (qui 0.5 = metà elemento visibile).
        - entries: array degli elementi osservati la cui visibilità è cambiata.
        - entry.target può essere UN <video> (GitHub/CDN) OPPURE UN <iframe> (Drive),
        mai entrambi: vanno gestiti separatamente in base al tag. */
    // var visibleVideos = new Set(); // Per tenere traccia dei video attualmente visibili (opzionale, per debug o autoplay se si vistiano altre pagine nel mentre)
    
    var observer = new IntersectionObserver(function (entries) {
        // ----- VIDEO NATIVO (GitHub/CDN) -----
        entries.forEach(function (entry) {
            var video = entry.target;
            if (entry.isIntersecting) {
                // play() torna una promise, rigettata (catch) se autoplay non è permesso.
                // Il <video> è muted, quindi l'autoplay è consentito dal browser.
                // visibleVideos.add(video); // Se si vuole tenere traccia dei video visibili (opzionale)
                video.play().catch(function () {});
            } else {
                // visibleVideos.delete(video); // Se si vuole tenere traccia dei video visibili (opzionale)
                video.pause();
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
        observer.observe(v);
    });

    // ---------------------- VIDEO MODE: CHANGE WEB PAGE--------------------------------
    // Pause the in-post video when the user clicks any external link (e.g. CTA button).
    // Utile solamente in caso il video rimanesse in background, altrimenti c'è già visibilitychange
    document.querySelectorAll('.insta-post a[target="_blank"]').forEach(function (link) {
        link.addEventListener('click', function () {
            var post = link.closest('.insta-post');
            if (!post) return;
            var video = post.querySelector('video[data-doc-id]');
            if (video) video.pause(); //visibleVideos.delete(video); // Se si tiene traccia dei video visibili (opzionale)
        });
    });

    // Pause every feed video when the tab is hidden. Query the DOM directly so we
    // catch videos started manually via controls (< 50% visible) and the initial-load
    // race, not just observer-triggered plays. No resume on return: by design videos
    // only restart when scrolled back into view.
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') {
            document.querySelectorAll('video[data-doc-id]').forEach(function (video) {
                video.pause();
            });
        }
        /* PER AUTOPLAY         
        } else {
            visibleVideos.forEach(function (video) {
                video.play().catch(function () {});
            });
        }*/        
    });

    // --------------------------------------------------------------------------

});


// IFRAME + VIDEO VERSION
/*
document.addEventListener('DOMContentLoaded', function () {
    var observer = new IntersectionObserver(function (entries) {
        
        entries.forEach(function (entry) {
            var el = entry.target;

            // ----- VIDEO NATIVO (GitHub/CDN) -----
            if (el.tagName === 'VIDEO') {
                if (entry.isIntersecting) {
                    // play() torna una promise, rigettata (catch) se autoplay non è permesso.
                    // Il <video> è muted, quindi l'autoplay è consentito dal browser.
                    el.play().catch(function () {});
                } else {
                    el.pause();
                }

            // ----- IFRAME GOOGLE DRIVE -----
            } else if (el.tagName === 'IFRAME') {
                // Cross-origin: non possiamo play()/pause() via JS. L'unica leva è il src.
                if (entry.isIntersecting) {
                    // Inietta il src solo quando entra in vista → carica + ?autoplay=1
                    // (best-effort: Drive non garantisce l'autoplay).
                    if (!el.src || el.src === window.location.href) {
                        el.src = el.getAttribute('data-drive-src');
                    }
                } else {
                    // Esce dalla vista → azzera il src per fermare il video Drive
                    // (altrimenti continuerebbe a suonare fuori schermo).
                    el.removeAttribute('src');
                }
            }
        });
    }, { threshold: 0.5 });

    // Osserva tutti i <video> nativi e tutti gli <iframe> Drive del feed
    document.querySelectorAll('video[data-doc-id], iframe[data-drive-src]').forEach(function (el) {
        observer.observe(el);
    });
});*/
