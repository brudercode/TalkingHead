# EcoChiefs Asset Pipeline

Complete pipeline for managing 3D assets from source → refinement → approval → publication in the EcoChiefs Oracle interface.

## Architecture

```
Source GLBs (Meshy/Blender)
       ↓
   ingest_asset (Windmill)
       ↓
Asset Registry (SQLite) ← registry.py CLI
       ↓
   run_refinery (Windmill)
       ↓
ComfyUI Refinement (optional)
       ↓
   qa_blender_master (Human QA)
       ↓
   approve/reject (registry.py)
       ↓
   publish_registry_entry (Windmill)
       ↓
Web Assets (/assets/taurus/*.glb)
       ↓
TaurusAvatarStage (TalkingHead)
       ↓
EcoChiefs Oracle UI
```

## Quick Start

```bash
cd pipeline/registry

# 1. Initialize registry
python3 registry.py init

# 2. Ingest Meshy GLBs
python3 registry.py ingest ../../assets/3d \
  --identity ecochief.taurus \
  --tool meshy

# 3. Query pending assets
python3 registry.py query --state pending

# 4. Approve an asset
python3 registry.py approve <asset_id> \
  --notes "Passed topology and identity review"

# 5. Publish to web (or use Windmill flow)
python3 registry.py publish <asset_id> \
  --web-path /assets/taurus/taurus-meshy-v1.glb

# 6. Bind to ArchCard slot
python3 registry.py bind <asset_id> \
  --slot avatar3d \
  --canonical
```

## Directory Structure

```
pipeline/
├── registry/
│   ├── schema.sql          # Database schema
│   ├── registry.py         # CLI tool
│   └── registry.db         # SQLite database (generated)
├── windmill/
│   └── flows/
│       ├── ingest_asset.yaml
│       ├── publish_registry_entry.yaml
│       ├── run_refinery.yaml
│       ├── qa_blender_master.yaml
│       └── route_defect.yaml
└── comfyui/
    ├── subgraphs/          # AI refinement workflows
    └── README.md
```

## Windmill Setup

1. Create `ecochiefs` workspace in Windmill
2. Import flows from `windmill/flows/`
3. Set these resource variables:
   - `REGISTRY_DB` = `/path/to/pipeline/registry/registry.db`
   - `COMFYUI_URL` = `http://127.0.0.1:8188`
   - `COMFYUI_OUTPUT` = `/path/to/ComfyUI/output`
   - `WEB_ASSETS_ROOT` = `/path/to/eco-chiefs-oracle/public/assets`
   - `WINDMILL_TOKEN` = `your_windmill_token`

## Asset States

- `pending` - Newly ingested, awaiting review
- `refining` - In ComfyUI refinement pipeline
- `review` - Ready for human QA
- `approved` - Passed QA, ready to publish
- `rejected` - Failed QA
- `superseded` - Replaced by newer version
- `published` - Live in production

## Registry CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize database |
| `ingest <path>` | Ingest GLB file(s) |
| `query` | List assets with filters |
| `approve <id>` | Approve asset |
| `reject <id>` | Reject asset |
| `publish <id>` | Mark as published |
| `bind <id>` | Bind to card slot |
| `defect <id>` | Log defect |
| `show <id>` | Show full asset details |

## Integration with TalkingHead

The `TaurusAvatarStage` component (in `eco-chiefs-oracle/src/lib/card/taurusSdk.js`) loads GLBs from paths defined in `card_bindings`:

```javascript
const taurus = new TaurusAvatarStage('canvas-id', {
    modelPath: '/assets/taurus/taurus-meshy-v1.glb'
});
await taurus.init();
```

The `publish_registry_entry` Windmill flow:
1. Copies approved GLB to `eco-chiefs-oracle/public/assets/<identity>/`
2. Updates `card_bindings` table with web path
3. Sets canonical binding for slot

## Defect Reporting

Report defects from browser viewer or Blender:

```bash
python3 registry.py defect <asset_id> \
  --type texture_seam \
  --severity medium \
  --desc "UV seam visible at left shoulder"
```

Defects trigger `route_defect` Windmill flow which dispatches to appropriate refinement subgraph or flags for manual Blender fix.

## EcoChiefs Identities

| Identity | ID | Description |
|----------|----|----|
| Taurus | `ecochief.taurus` | Chief Guardian of Value & Stewardship |
| Fox | `ecochief.fox` | Clever Strategist |
| Khan | `ecochief.khan` | Wise Leader |
| Kong | `ecochief.kong` | Mighty Protector |
| Rocky | `ecochief.rocky` | Steadfast Guardian |
| Rudi | `ecochief.rudi` | Swift Scout |
| Ruki | `ecochief.ruki` | Resourceful Planner |
| Tusker | `ecochief.tusker` | Ancient Keeper |

## Next Steps

1. ✅ Registry scaffold - **DONE**
2. ✅ TaurusAvatarStage component - **DONE**
3. ⬜ Test end-to-end flow with real GLB
4. ⬜ Wire Windmill flows to real ComfyUI instance
5. ⬜ Build defect routing logic
6. ⬜ Add LLM oracle backend integration
7. ⬜ Deploy to production
