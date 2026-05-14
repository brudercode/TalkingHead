# Guide: Creating Talking Animals with TalkingHead

This guide explains how to support non-humanoid or "waist-up" animal avatars in the TalkingHead library.

## 1. Avatar Rigging Requirements

To make an animal "talk" and move, it should ideally follow these rigging standards:

### Morph Targets (Blend Shapes)
The library uses standard visemes for lip-sync. Ensure your animal model has the following blend shapes (following the Ready Player Me / Oculus standard):
*   **Visemes:** `viseme_aa`, `viseme_E`, `viseme_I`, `viseme_O`, `viseme_U`, `viseme_PP`, `viseme_SS`, `viseme_TH`, etc.
*   **Expressions:** `browInnerUp`, `browOuterUpLeft`, `browOuterUpRight`, `eyeWideLeft`, `eyeWideRight`, `jawOpen`, `mouthPucker`, `mouthSmile`.

### Bone Structure
By default, the library expects a full humanoid rig. For animals:
1.  **Map Primary Bones:** Rename your animal's main joints to:
    *   `Hips` (Base of spine)
    *   `Spine`, `Spine1`, `Spine2`
    *   `Neck`
    *   `Head` (The parent of the face/jaw)
2.  **Blender Helpers:** Check the `/blender` directory for scripts like `rename-tomcat-shapekeys.py` to help automate renaming for specific base rigs.
3.  **Waist-up Animals:** If your model is only a bust, it should ideally have the following minimum hierarchy: `Hips` -> `Spine` -> `Neck` -> `Head`.

## 2. Enabling Non-Humanoid Support (Library Changes)

The library currently enforces a strict humanoid bone set. To support animals with fewer bones, the following change is required in `modules/talkinghead.mjs`:

### Change `showAvatar` Validation
Modify the validation loop in `showAvatar` to define a minimum set of required bones (e.g., `Head` and `Neck`) and treat others as optional.

*In `modules/talkinghead.mjs`:*

```javascript
// 1. Update validation loop (around line 1201)
const required = [ this.opt.modelRoot, 'Head', 'Neck' ];
// Only these are strictly required now.
required.forEach( x => {
  if ( !gltf.scene.getObjectByName(x) ) {
    throw new Error('Avatar object ' + x + ' not found');
  }
});

// 2. Update property mapping (around line 1307)
this.posePropNames.forEach( x => {
  const ids = x.split('.');
  const o = this.armature.getObjectByName(ids[0]);
  if (o) { // Check if the bone exists in the rig
    this.poseAvatar.props[x] = o[ids[1]];
    // ... rest of the copy logic
  }
});
```

## 3. Animating Ears, Tails, and Whiskers

Use the `DynamicBones` system for automatic secondary motion. In your avatar configuration object:

```javascript
const avatar = {
  url: 'path/to/animal.glb',
  modelDynamicBones: [
    {
      bone: "Ear_L",
      type: "link",
      stiffness: 0.5,
      damping: 0.5
    },
    {
      bone: "Tail_1",
      type: "link",
      stiffness: 0.3,
      damping: 0.4
    }
  ]
};
```

## 4. Customizing Poses for Animals

If the default "straight" pose doesn't fit your animal (e.g., a bird or a cat), you can override the `poseTemplates` in the constructor or by modifying `this.poseStraight` after loading.

1.  **Neutral State:** Ensure the animal looks "forward" in its rest state.
2.  **Rotation Offsets:** Animals often have different neck-to-head angles. Adjust the `Neck.rotation` and `Head.rotation` in the `straight` template.

---
*Note: This guide assumes the library has been patched to allow missing bones.*
