/* Conference page: an honest contact form.
   The original button waited 700 ms and printed "Message sent" without sending anything.
   A static site has no server, so we hand the message to the visitor's email app instead. */
(function () {
  'use strict';
  var TO = 'info@ac-tlc.org';

  function field(box, sel) { var el = box.querySelector(sel); return el ? el.value.trim() : ''; }

  window.handleConferenceForm = function (btn) {
    var box = btn.closest('.cf') || document;
    var ok = document.getElementById('cf-ok');
    var email = box.querySelector('#cf-email'), msg = box.querySelector('#cf-message');
    var missing = [];
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) missing.push(email);
    if (!msg || !msg.value.trim()) missing.push(msg);
    if (missing.length) {
      ok.className = 'is-error';
      ok.textContent = missing[0] === email
        ? 'Add a valid email address so we can reply.'
        : 'Write a short message before sending.';
      ok.style.display = 'block';
      missing[0] && missing[0].focus();
      return;
    }
    var name = [field(box, '#cf-first'), field(box, '#cf-last')].filter(Boolean).join(' ');
    var type = field(box, '#cf-type') || 'General enquiry';
    var body = msg.value.trim() + '\n\n' + [name, field(box, '#cf-org'), email.value.trim()].filter(Boolean).join('\n');
    var url = 'mailto:' + TO + '?subject=' + encodeURIComponent('ACTLC 2027 conference: ' + type) +
              '&body=' + encodeURIComponent(body);
    btn.setAttribute('data-mailto', url);
    ok.className = '';
    ok.textContent = 'Your email app should open with this message ready to send. If it doesn’t, write to ' + TO + '.';
    ok.style.display = 'block';
    window.location.href = url;
  };
})();
