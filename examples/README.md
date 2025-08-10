# Examples

## pdf_tools Admin Dashboard Demo

Start the pdf_tools service separately, then run:

```bash
python examples/run_pdf_tools_admin.py
```

Visit `http://localhost:5000/admin/plugins` to see the registry poll the
`pdf_tools` service for health, info and metrics.

## Embedded Plugin Demo

Run a dummy embedded plugin:

```bash
python examples/run_embedded_dummy.py
```

This registers an in-process blueprint and the admin page will list it along
with its health and metrics.
