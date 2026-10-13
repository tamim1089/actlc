// Run: node --test tools/test_events.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../actlc-assets/events.js');

const at = (iso) => Date.parse(iso);
const START = at('2026-10-19T16:30:00+04:00'); // Designing AI-Ready Graduates
const END = at('2026-10-19T18:00:00+04:00');

test('phase: upcoming, live at start, past at end', () => {
  assert.equal(E.phase(START - 1, START, END), 'upcoming');
  assert.equal(E.phase(START, START, END), 'live');
  assert.equal(E.phase(END - 1, START, END), 'live');
  assert.equal(E.phase(END, START, END), 'past');
});

test('relativeStart: minutes, hours, tomorrow, days', () => {
  assert.equal(E.relativeStart(START - 20 * 6e4, START, 'Asia/Dubai'), 'in 20 minutes');
  assert.equal(E.relativeStart(START - 3 * 36e5, START, 'Asia/Dubai'), 'in 3 hours');
  assert.equal(E.relativeStart(at('2026-10-18T20:00:00+04:00'), START, 'Asia/Dubai'), 'tomorrow');
  assert.equal(E.relativeStart(at('2026-10-13T14:00:00+04:00'), START, 'Asia/Dubai'), 'in 6 days');
});

test('relativeStart counts calendar days in the visitor timezone', () => {
  // 13:00 UTC on 17 Oct: still 17 Oct in New York, already 18 Oct (17:00) in Dubai.
  const now = at('2026-10-17T21:00:00+00:00');
  assert.equal(E.relativeStart(now, START, 'Asia/Dubai'), 'tomorrow');      // 18 -> 19
  assert.equal(E.relativeStart(now, START, 'America/New_York'), 'in 2 days'); // 17 -> 19
});

test('statusText', () => {
  assert.equal(E.statusText(END + 1, START, END, 'Asia/Dubai'), 'Ended');
  assert.equal(E.statusText(START + 1, START, END, 'Asia/Dubai'), 'Live now');
  assert.match(E.statusText(START - 36e5 * 30, START, END, 'Asia/Dubai'), /^Starts /);
});

test('member country clock on the session date (tzdata 2026c: Morocco +00 from 2026-09-20)', () => {
  assert.equal(E.clock(START, 'Asia/Dubai'), '16:30');
  assert.equal(E.clock(START, 'Asia/Riyadh'), '15:30');
  assert.equal(E.clock(START, 'Asia/Bahrain'), '15:30');
  assert.equal(E.clock(START, 'Africa/Cairo'), '15:30'); // Egypt summer time until late October
  // Morocco depends on the runtime's tz database; report rather than hard-fail on old ICU data.
  const ma = E.clock(START, 'Africa/Casablanca');
  assert.ok(ma === '12:30' || ma === '13:30', 'Morocco ' + ma);
  if (ma !== '12:30') console.log('note: this runtime has pre-2026c tz data for Morocco (' + ma + ')');
});

test('memberCode and cityFromTz', () => {
  assert.equal(E.memberCode('Asia/Dubai'), 'ae');
  assert.equal(E.memberCode('Africa/Casablanca'), 'ma');
  assert.equal(E.memberCode('Asia/Kuwait'), null);
  assert.equal(E.cityFromTz('America/New_York'), 'New York');
  assert.equal(E.cityFromTz('America/Argentina/Buenos_Aires'), 'Buenos Aires');
});

test('dayMarker: next and previous day like World Clock', () => {
  assert.equal(E.dayMarker(START, 'Asia/Dubai', 'Asia/Dubai'), '');
  assert.equal(E.dayMarker(START, 'Asia/Dubai', 'America/Los_Angeles'), '');   // 05:30 same day
  assert.equal(E.dayMarker(START, 'Asia/Dubai', 'Pacific/Kiritimati'), 'Next day'); // 02:30 next day
  const early = at('2026-10-19T01:00:00+04:00');
  assert.equal(E.dayMarker(early, 'Asia/Dubai', 'America/New_York'), 'Previous day'); // 17:00 on 18 Oct
});
