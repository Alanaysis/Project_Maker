/**
 * Basic Timeline Example
 *
 * Demonstrates basic timeline creation, keyframe animation,
 * playback controls, and state computation.
 */

import { Timeline, KeyframeEntry, Easing } from '../src/index';

// Create a timeline
const timeline = new Timeline({
  duration: 2000,
  fps: 60,
});

// Add a position animation
timeline.addKeyframe({
  name: 'x-position',
  property: 'x',
  keyframes: [
    { time: 0, value: 0 },
    { time: 0.5, value: 200 },
    { time: 1, value: 100 },
  ],
  duration: 2000,
  easing: Easing.easeInOutCubic,
});

// Add an opacity animation
timeline.addKeyframe({
  name: 'opacity',
  property: 'opacity',
  keyframes: [
    { time: 0, value: 0 },
    { time: 0.3, value: 1 },
    { time: 0.7, value: 1 },
    { time: 1, value: 0 },
  ],
  duration: 2000,
  easing: 'linear',
});

// Add a scale animation
timeline.addKeyframe({
  name: 'scale',
  property: 'scale',
  keyframes: [
    { time: 0, value: 0.5 },
    { time: 0.5, value: 1.5 },
    { time: 1, value: 1 },
  ],
  duration: 2000,
  easing: Easing.easeOutQuad,
});

// Add a rotation animation
timeline.addKeyframe({
  name: 'rotation',
  property: 'rotation',
  keyframes: [
    { time: 0, value: 0 },
    { time: 1, value: 360 },
  ],
  duration: 2000,
  easing: 'linear',
});

// Demo playback
console.log('=== Basic Timeline Demo ===');

// Show state at different points
const checkpoints = [0, 0.25, 0.5, 0.75, 1];
for (const p of checkpoints) {
  timeline.seek(p);
  const state = timeline.getState();
  console.log(`Progress ${p * 100}%: x=${state.x.toFixed(1)}, opacity=${state.opacity.toFixed(2)}, scale=${state.scale.toFixed(2)}, rotation=${state.rotation.toFixed(1)}deg`);
}

// Demo play/pause/stop
console.log('\n=== Playback Demo ===');
timeline.play();
console.log('Playing...');

// Simulate pause at 25%
setTimeout(() => {
  timeline.pause();
  console.log(`Paused at progress ${timeline.getProgress().toFixed(2)}`);
  console.log(`State: x=${timeline.getState().x.toFixed(1)}`);

  // Resume
  setTimeout(() => {
    timeline.play();
    console.log('Resumed...');

    // Seek to end
    setTimeout(() => {
      timeline.seek(1);
      console.log(`Stopped at progress ${timeline.getProgress().toFixed(2)}`);
      console.log(`Final state: x=${timeline.getState().x.toFixed(1)}`);

      // Reset
      timeline.stop();
      console.log('Timeline stopped and reset.');

      // Cleanup
      timeline.destroy();
      console.log('=== Demo Complete ===');
    }, 100);
  }, 100);
}, 100);
