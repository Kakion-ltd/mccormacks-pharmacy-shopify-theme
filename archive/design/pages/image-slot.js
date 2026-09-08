// <image-slot> shim: shows the supplied hero photo for known slots,
// otherwise the striped "photo pending" placeholder from the README.
(() => {
  const IMAGES = {
    'hero-travel': 'assets/hero-summer-travel.jpg',
    'hero-feelbest': 'assets/slide-vitamins.jpg',
    'hero-skincare': 'assets/slide-skincare.jpg',
    'hero-baby': 'assets/slide-baby.jpg',
    'hero-gifts': 'assets/slide-fragrance.jpg',
  };
  customElements.define('image-slot', class extends HTMLElement {
    connectedCallback() {
      this.style.cssText = 'position:absolute; inset:0; display:block; overflow:hidden;';
      const src = IMAGES[this.id];
      this.innerHTML = src
        ? `<img src="${src}" alt="" style="width:100%; height:100%; object-fit:cover; display:block;">`
        : `<div style="position:absolute; inset:0; display:flex; align-items:center; justify-content:center; text-align:center; padding:16px; color:#5a6153; font-size:13px; background:repeating-linear-gradient(45deg,#eef3e6 0 12px,#e2ead4 12px 24px);">${this.getAttribute('placeholder') || ''}</div>`;
    }
  });
})();
