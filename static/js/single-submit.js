// Stop login/register forms from being sent twice (double click or Enter + click).
// A second submit after a successful login carries the old CSRF token and fails with 403.
document.querySelectorAll('form[method="post"]').forEach(function (form) {
  form.addEventListener('submit', function (event) {
    if (form.dataset.submitting === 'true') {
      event.preventDefault();
      return;
    }
    form.dataset.submitting = 'true';
    form.querySelectorAll('button[type="submit"]').forEach(function (button) {
      button.setAttribute('aria-disabled', 'true');
      button.style.opacity = '0.6';
      button.style.cursor = 'progress';
    });
  });
});
// Coming back with the browser Back button restores the page from cache; allow submitting again.
window.addEventListener('pageshow', function (event) {
  if (event.persisted) {
    document.querySelectorAll('form[data-submitting]').forEach(function (form) {
      delete form.dataset.submitting;
    });
  }
});
