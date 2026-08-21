For content that interrupts: the info sheet, the unmatched quick view.

```jsx
<Modal title="Welcome to ScrobbleScope" onClose={close} footer={<Button variant="primary">Get started</Button>}>
  <p>Discover your top albums from Last.fm…</p>
</Modal>
```

Notes
- The dialog is absolutely positioned inside its nearest positioned ancestor so it works inside device frames; in a real page make that ancestor the viewport.
- On mobile the shell should go full-width minus 16px, matching the shipped `.modal-dialog` override.
- Body scrolls, header and footer stay fixed. Never nest a second modal.
