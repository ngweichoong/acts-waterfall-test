(() => {
  const el = document.querySelector('.event-image.bible-study-image');
  if (!el) return;

  const parts = [
    'assets/bible-study-live/p0a.txt',
    'assets/bible-study-live/p0b.txt',
    'assets/bible-study-live/p1.txt',
    'assets/bible-study-live/p2.txt',
    'assets/bible-study-live/p3a.txt',
    'assets/bible-study-live/p3b.txt'
  ];

  Promise.all(parts.map((src) =>
    fetch(src, { cache: 'force-cache' }).then((response) => {
      if (!response.ok) throw new Error(`Failed to load ${src}`);
      return response.text();
    })
  ))
    .then((chunks) => {
      const base64 = chunks.join('').replace(/\s+/g, '');
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);

      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }

      const imageUrl = URL.createObjectURL(
        new Blob([bytes], { type: 'image/webp' })
      );

      el.style.backgroundImage = `url("${imageUrl}")`;
      el.dataset.hdLoaded = 'true';
    })
    .catch((error) => {
      console.error('Bible study banner failed to load:', error);
    });
})();