# ComfyUI Subgraphs for EcoChiefs Asset Pipeline

This directory contains ComfyUI workflow subgraphs for AI-powered asset refinement.

## Subgraphs

### `texture_candidate.json`
Generates PBR texture candidates using ControlNet depth + normal guidance.

**Inputs:**
- Source portrait image
- Depth map (auto-generated)
- Normal map (auto-generated)

**Outputs:**
- Refined texture candidate (registered back to asset registry)

### `turnaround_4view.json` 
Generates 4-view character turnaround from single portrait.

**Inputs:**
- Source portrait

**Outputs:**
- Front, side, back, 3/4 view renders

## Adding New Subgraphs

1. Design workflow in ComfyUI UI
2. Export as API JSON
3. Save to `subgraphs/`
4. Add token references (see below)
5. Call from Windmill `run_refinery` flow

## Token Reference

Subgraphs can use these tokens (replaced by Windmill at runtime):

- `{{ASSET_ID}}` - Current asset UUID
- `{{IDENTITY_ID}}` - Identity (e.g., `ecochief.taurus`)
- `{{SOURCE_PATH}}` - Path to source GLB
- `{{OUTPUT_DIR}}` - ComfyUI output directory
- `{{REGISTRY_DB}}` - Path to registry database

Example:
```json
{
  "save_image": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "{{ASSET_ID}}_refined"
    }
  }
}
```

## ComfyUI Setup

1. Install ComfyUI: `git clone https://github.com/comfyanonymous/ComfyUI`
2. Install custom nodes:
   - ControlNet
   - Depth estimator
   - Normal map generator
3. Start server: `python main.py --listen 0.0.0.0`
4. Set `COMFYUI_URL` in Windmill resources

## Workflow Integration

```
Asset → run_refinery flow → Load subgraph → Replace tokens → 
POST to ComfyUI API → Monitor progress → Register output → 
Update registry state
```
