/* ========= Smooth Scroll ========= */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    document.querySelector(this.getAttribute('href'))
      .scrollIntoView({ behavior: 'smooth' });
  });
});

/* ========= Certificate Modal ========= */
const certBtn = document.querySelector('.btn-secondary');
const modal = document.createElement('div');

if (certBtn) {
  modal.innerHTML = `
    <div class="modal-overlay">
      <div class="modal-content">
        <span class="close-modal">&times;</span>
        <iframe src="certificate/certificate.html"></iframe>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  certBtn.addEventListener('click', e => {
    e.preventDefault();
    modal.classList.add('show');
  });

  modal.addEventListener('click', e => {
    if (
      e.target.classList.contains('modal-overlay') ||
      e.target.classList.contains('close-modal')
    ) {
      modal.classList.remove('show');
    }
  });
}
