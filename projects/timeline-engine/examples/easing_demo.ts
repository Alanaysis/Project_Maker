/**
 * Easing Functions Demo
 *
 * Demonstrates all available easing functions and their visual characteristics.
 */

import {
  linear,
  easeInQuad,
  easeOutQuad,
  easeInOutQuad,
  easeInCubic,
  easeOutCubic,
  easeInOutCubic,
  easeInQuart,
  easeOutQuart,
  easeInOutQuart,
  easeInQuint,
  easeOutQuint,
  easeInOutQuint,
  easeInSine,
  easeOutSine,
  easeInOutSine,
  easeInExpo,
  easeOutExpo,
  easeInOutExpo,
  easeInCirc,
  easeOutCirc,
  easeInOutCirc,
  easeInElastic,
  easeOutElastic,
  easeInOutElastic,
  easeInBack,
  easeOutBack,
  easeInOutBack,
  easeInBounce,
  easeOutBounce,
  easeInOutBounce,
  resolveEasing,
  getEasingNames,
} from '../src/index';

// Easing functions to demo
const easings: Array<{ name: string, fn: (t: number) => number }> = [
  { name: 'linear', fn: linear },
  { name: 'easeInQuad', fn: easeInQuad },
  { name: 'easeOutQuad', fn: easeOutQuad },
  { name: 'easeInOutQuad', fn: easeInOutQuad },
  { name: 'easeInCubic', fn: easeInCubic },
  { name: 'easeOutCubic', fn: easeOutCubic },
  { name: 'easeInOutCubic', fn: easeInOutCubic },
  { name: 'easeInQuart', fn: easeInQuart },
  { name: 'easeOutQuart', fn: easeOutQuart },
  { name: 'easeInOutQuart', fn: easeInOutQuart },
  { name: 'easeInQuint', fn: easeInQuint },
  { name: 'easeOutQuint', fn: easeOutQuint },
  { name: 'easeInOutQuint', fn: easeInOutQuint },
  { name: 'easeInSine', fn: easeInSine },
  { name: 'easeOutSine', fn: easeOutSine },
  { name: 'easeInOutSine', fn: easeInOutSine },
  { name: 'easeInExpo', fn: easeInExpo },
  { name: 'easeOutExpo', fn: easeOutExpo },
  { name: 'easeInOutExpo', fn: easeInOutExpo },
  { name: 'easeInCirc', fn: easeInCirc },
  { name: 'easeOutCirc', fn: easeOutCirc },
  { name: 'easeInOutCirc', fn: easeInOutCirc },
  { name: 'easeInElastic', fn: easeInElastic },
  { name: 'easeOutElastic', fn: easeOutElastic },
  { name: 'easeInOutElastic', fn: easeInOutElastic },
  { name: 'easeInBack', fn: easeInBack },
  { name: 'easeOutBack', fn: easeOutBack },
  { name: 'easeInOutBack', fn: easeInOutBack },
  { name: 'easeInBounce', fn: easeInBounce },
  { name: 'easeOutBounce', fn: easeOutBounce },
  { name: 'easeInOutBounce', fn: easeInOutBounce },
];

console.log('=== Easing Functions Demo ===\n');

// Show boundary conditions
console.log('Boundary Conditions (t=0 and t=1):');
for (const { name, fn } of easings) {
  const at0 = fn(0).toFixed(6);
  const at1 = fn(1).toFixed(6);
  const ok0 = Math.abs(fn(0)) < 1e-10 ? 'OK' : 'FAIL';
  const ok1 = Math.abs(fn(1) - 1) < 1e-10 ? 'OK' : 'FAIL';
  console.log(`  ${name}: f(0)=${at0} [${ok0}], f(1)=${at1} [${ok1}]`);
}

// Show mid-point values
console.log('\nMid-point Values (t=0.5):');
for (const { name, fn } of easings) {
  const val = fn(0.5).toFixed(4);
  console.log(`  ${name}: ${val}`);
}

// Show registered easing names
console.log('\nRegistered Easing Names:');
const names = getEasingNames();
console.log(`  Total: ${names.length} named easings`);
console.log(`  First 5: ${names.slice(0, 5).join(', ')}...`);

// Demo resolveEasing
console.log('\nresolveEasing Demo:');
const resolved1 = resolveEasing('ease-out-cubic');
const resolved2 = resolveEasing((t: number) => t * t);
const resolved3 = resolveEasing(undefined);
console.log(`  Named "ease-out-cubic": f(0.5) = ${resolved1(0.5).toFixed(4)}`);
console.log(`  Custom function: f(0.5) = ${resolved2(0.5).toFixed(4)}`);
console.log(`  Default (undefined): f(0.5) = ${resolved3(0.5).toFixed(4)}`);

console.log('\n=== Easing Demo Complete ===');
