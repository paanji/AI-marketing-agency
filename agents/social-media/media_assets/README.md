# Media Assets

Drop client photos here, one subfolder per item or announcement:

```
media_assets/
  glow-fresh-launch/
    1.jpg
    2.jpg
```

Then point a `manual_announcements` entry's `media_folder` key (or a catalog
item's mapped `media_folder_field`) at the subfolder name (e.g.
`"glow-fresh-launch"`) and video generation picks it up automatically the
next time the agent runs.

If no folder is found for a given item, video generation is silently
skipped -- the platform just falls back to its text `media_brief` instead.
Nothing ever blocks on missing photos.
