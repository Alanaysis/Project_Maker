/**
 * Timeline Demo
 *
 * Demonstrates advanced timeline features including animation clips,
 * multiple properties, and event handling.
 */

import { Timeline, Easing, AnimationClip } from '../src/index';

console.log('=== Timeline Advanced Demo ===\n');

// Create timeline with loop
const timeline = new Timeline({
  duration: 3000,
  fps: 60,
  loop: true,
});

// Add animation clip
const slideClip = new AnimationClip({
  name: 'slide-in',
  animations: [
    {
      property: 'x',
      keyframes: [
        { time: 0, value: -200 },
        { time: 0.3, value: 0 },
        { time: 0.7, value: 0 },
        { time: 1, value: 200 },
      ],
      easing: 'ease-out-cubic',
    },
    {
      property: 'opacity',
      keyframes: [
        { time: 0, value: 0 },
        { time: 0.1, value: 1 },
        { time: 0.9, value: 1 },
        { time: 1, value: 0 },
      ],
      easing: 'linear',
    },
  ],
  duration: 3000,
});

timeline.addClip(slideClip);

// Add keyframe animations
timeline.addKeyframe({
  name: 'scale-anim',
  property: 'scale',
  keyframes: [
    { time: 0, value: 0.5 },
    { time: 0.5, value: 1.5 },
    { time: 1, value: 1 },
  ],
  duration: 3000,
  easing: Easing.easeOutBounce,
});

timeline.addKeyframe({
  name: 'rotation-anim',
  property: 'rotation',
  keyframes: [
    { time: 0, value: 0 },
    { time: 1, value: 720 },
  ],
  duration: 3000,
  easing: 'linear',
});

// Event handlers
let playCount = 0;
let completeCount = 0;

timeline.on('play', () => {
  playCount++;
  console.log(`[Event] Play #${playCount} at time ${timeline.getCurrentTime()}ms`);
});

timeline.on('complete', () => {
  completeCount++;
  console.log(`[Event] Complete #${completeCount} at time ${timeline.getCurrentTime()}ms`);
});

timeline.on('frame', (data: any) => {
  // Log first few frames
  if (data.time < 100) {
    console.log(`[Frame] time=${data.time.toFixed(1)}ms, progress=${data.progress.toFixed(3)}`);
  }
});

// Demo
console.log('Starting timeline...');
timeline.play();

// Seek to different points
setTimeout(() => {
  console.log('\n--- Seeking to 25% ---');
  timeline.seek(0.25);
  const state = timeline.getState();
  console.log(`State: x=${state.x?.toFixed(1)}, opacity=${state.opacity?.toFixed(2)}, scale=${state.scale?.toFixed(2)}, rotation=${state.rotation?.toFixed(1)}`);
}, 50);

setTimeout(() => {
  console.log('\n--- Seeking to 75% ---');
  timeline.seek(0.75);
  const state = timeline.getState();
  console.log(`State: x=${state.x?.toFixed(1)}, opacity=${state.opacity?.toFixed(2)}, scale=${state.scale?.toFixed(2)}, rotation=${state.rotation?.toFixed(1)}`);
}, 100);

setTimeout(() => {
  console.log('\n--- Pausing ---');
  timeline.pause();
  console.log(`Paused at progress ${timeline.getProgress().toFixed(3)}`);
}, 150);

setTimeout(() => {
  console.log('\n--- Resuming ---');
  timeline.play();
}, 200);

setTimeout(() => {
  console.log('\n--- Stopping ---');
  timeline.stop();
  console.log(`Stopped at progress ${timeline.getProgress().toFixed(3)}`);
  console.log(`Play events: ${playCount}, Complete events: ${completeCount}`);
}, 250);

setTimeout(() => {
  timeline.destroy();
  console.log('\n=== Demo Complete ===');
}, 300);
