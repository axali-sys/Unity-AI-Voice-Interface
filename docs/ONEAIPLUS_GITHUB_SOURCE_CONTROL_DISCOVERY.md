# Oneaiplus GitHub Source-Control Discovery

Date: 2026-11-14

## Findings

### Canonical Oneaiplus Lovable project

- Project ID: `c2232890-a16d-4289-b2f8-c8de6365a7b4`
- Current source stack: TanStack Start, TypeScript, React, Tailwind CSS
- Current base commit: `3fac96efc001f394622301568f2f42417c08a87a`
- Its current `README.md` is the generic Lovable starter README. It instructs the owner to connect the project to GitHub but does not name a repository or confirm an existing source-control link.
- The Lovable project metadata available through the integration does not expose a linked repository or branch field.

### Existing OneAI Workspace repository

- Repository: https://github.com/axali-sys/oneai-workspace
- Visibility: private
- Default branch: `main`
- Repository README explicitly links to Lovable project `c7f1e64a-d093-4b2c-9c09-7b8a47bbd2f6` (OneAI Workspace).
- Its README describes a combined project built from the original Pixel Perfect and Pixel-Perfect Replica projects and says Lovable changes sync to this repository.
- Its package manifest uses TanStack Start, TypeScript and React.

This proves that `oneai-workspace` is the source repository for the **OneAI Workspace donor project**, not for the canonical Oneaiplus project.

### XParallel source repository

- Repository: https://github.com/axali-sys/Unity-AI-Voice-Interface
- This is the existing XParallel / Unity AI backend and frontend source repository.
- It is not proven to be the canonical Oneaiplus TanStack Start repository.

## Safe conclusion

No existing GitHub repository has yet been verified as the source-control repository for the canonical Oneaiplus Lovable project. Do not point Oneaiplus at `oneai-workspace` or `Unity-AI-Voice-Interface` as its source-control repository merely because they are related.

## Next safe connection sequence

1. In the canonical Oneaiplus Lovable editor, open project settings / GitHub integration.
2. Check whether GitHub is already connected. If not, initiate the supported connection flow.
3. Select or create a dedicated repository named `oneaiplus` only after confirming the account and repository destination.
4. Verify the initial pushed commit and branch by reading the repository metadata and comparing the source files with the current Oneaiplus Lovable commit.
5. Do not replace existing repo contents, import XParallel code over the app, or merge donor history destructively.
6. Port donor features selectively after the canonical source is safely linked.

## Safety status

This was a read-only discovery of Lovable project metadata and GitHub repository metadata/content. No repository was created, no branch was changed, no project was linked, and no source code was edited. No production deployment, paid service, Render connection, or Vercel connection was performed.
