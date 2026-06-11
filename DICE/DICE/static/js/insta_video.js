document.addEventListener('DOMContentLoaded', function () {
    /* observer: API browser che controlla se gli elementi osservati attraversano
           la soglia di visibilità (qui 0.5 = metà elemento visibile).
           - entries: array degli elementi osservati la cui visibilità è cambiata.
           - entry.target può essere UN <video> (GitHub/CDN) OPPURE UN <iframe> (Drive),
             mai entrambi: vanno gestiti separatamente in base al tag. */
    var observer = new IntersectionObserver(function (entries) {
        // ----- VIDEO NATIVO (GitHub/CDN) -----
        entries.forEach(function (entry) {
            var video = entry.target;
            if (entry.isIntersecting) {
                // play() torna una promise, rigettata (catch) se autoplay non è permesso.
                // Il <video> è muted, quindi l'autoplay è consentito dal browser.
                video.play().catch(function () {});
            } else {
                video.pause();
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
        observer.observe(v);
    });
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
