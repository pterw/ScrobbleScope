Inline status attached to content. Use for "no albums matched", partial-data warnings and fetch failures.

```jsx
<Alert tone="warning" title="Partial data" action={<Button size="sm">Retry</Button>}>
  Last.fm returned 41 of 45 pages. Counts may be low.
</Alert>
```

Notes: always say what happened and what to do next. An alert with no next step should be a plain paragraph instead.
