Fires when an export finishes — the only place ScrobbleScope uses transient notification.

```jsx
<ToastStack>
  <Toast title="Exported" message="top-albums-2025.csv saved to Downloads" onClose={dismiss} />
</ToastStack>
```

Notes
- The tone is carried by a 3px vertical rule and the mono kicker, not by a tinted card background.
- Never use a toast for an error the user must act on — that belongs inline on the screen.
