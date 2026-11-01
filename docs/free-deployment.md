# Free online demo deployment

This repository is configured for a Render Static Site, a Render Free Web Service, Neon Free Postgres, and Neon Object Storage's included free allowance. No cloud resources are created by this repository change. Do not add a payment method or select a paid plan for this demo.

## Before deploying

1. Commit and push the project to a Git provider that Render can access. The existing local `.env` files must remain untracked; never put credentials in Git.
2. In Neon, create a **Free** project in one of the supported Object Storage regions. The database and the storage bucket should use the same project and branch.
3. In the Neon project, create a **private** bucket named `iq-ai-resumes`.
4. Create a branch-scoped credential with `storage:read` and `storage:write` access. Copy the S3 endpoint, region, access key ID, and secret access key from Neon. These are secret or project-specific values; enter them only in the Render backend environment dashboard.
5. Copy the Neon Postgres connection string for the same branch. Use the direct connection string (not a pooled hostname) and preserve its SSL query parameters. Paste it only in Render's backend `DATABASE_URL` field.

Neon currently includes 5 GB of Object Storage per Free project. Supported storage regions currently include AWS us-east-2 (Ohio), us-east-1 (N. Virginia), eu-central-1 (Frankfurt), and ap-southeast-1 (Singapore). The configured Blueprint defaults the SDK region to `us-east-2`; if your Neon project is in another supported region, change `AWS_REGION` in Render to the region returned by Neon.

## Create the Render services

1. In Render Dashboard, choose **New + → Blueprint** and connect the Git repository containing this project.
2. Render reads the root `render.yaml`. Confirm both services use the **Free** plan: `iq-ai-api` and `iq-ai-frontend`. The Blueprint does not define a Render database.
3. Supply these values when Render prompts for backend environment values, or add them under the backend service's **Environment** tab:

   | Variable | Value/source |
   | --- | --- |
   | `DATABASE_URL` | Neon branch connection string; keep it secret |
   | `GEMINI_API_KEY` | Optional Google AI Studio key; backend only; AI actions report a configuration/quota error when unavailable |
   | `AWS_ENDPOINT_URL_S3` | Neon branch's S3 endpoint URL |
   | `AWS_ACCESS_KEY_ID` | Neon storage credential's `token_id` |
   | `AWS_SECRET_ACCESS_KEY` | Neon storage credential's S3 secret |
   | `AWS_REGION` | Neon storage region; default in Blueprint is `us-east-2` |
   | `AWS_BUCKET_NAME` | Private Neon bucket name; default is `iq-ai-resumes` |

   Render generates `JWT_SECRET_KEY`. The CORS allowlist is set to the frontend URL in `render.yaml`. If Render changes a service's generated hostname because that name is unavailable, update **both** backend `FRONTEND_URL` and `CORS_ORIGINS`, and update frontend `VITE_API_BASE_URL` to `https://<actual-api-host>/api/v1`; then redeploy both services.

4. The backend's build command installs `backend/requirements.txt`. Its start command runs `alembic upgrade head` before Uvicorn, listening on Render's `$PORT`. The health check is `/health`.
5. The frontend runs `npm ci && npm run build`, publishes `frontend/dist`, and rewrites SPA routes to `/index.html`. Its API base URL is injected at build time.
6. After the first deploy, open the backend's `/health` URL, then the frontend URL. In the backend deploy logs, confirm the Alembic upgrade completed. Keep the Neon project and bucket private; never paste any secret into chat or frontend environment variables.

## Free-tier behavior and limits

- Render Free web services spin down after 15 minutes without inbound traffic. The first request afterward can take about a minute while the service starts. Render provides 750 free instance hours per workspace per month; usage is shared with other free web services in that workspace.
- Render Free web service disks are ephemeral. The app uses Neon Object Storage for resume bytes when deployed with this Blueprint. If storage credentials or the bucket are missing, upload fails with a clear configuration error instead of silently saving a non-durable file. Local development continues to use `backend/uploads`.
- Neon Free currently includes 100 CU-hours per project, 1 GB Postgres storage per project (20 GB total per account), 5 GB public network transfer per project, scale-to-zero after 5 idle minutes, 6 hours of history (up to 1 GB of changes), one manual snapshot, one day of monitoring history, and 5 GB of Object Storage per project. Watch the Neon usage dashboard; hitting a free limit can suspend or constrain service until the allowance resets. Do not upgrade to a paid plan for this demo.
- Resume files contain personal information. The bucket is private and backend-only. Neon Object Storage currently stores lifecycle/versioning settings but does not enforce expiration/versioning rules; delete test resumes manually when no longer needed. Neon storage is branch-aware, so keep the Render credential tied to the same Neon branch as the bucket.
- Gemini's free quota and model availability are controlled by Google and can change. The app should be treated as unable to perform AI actions when the key is missing, quota is exhausted, or the provider is unavailable; no paid billing is enabled by this setup.
- Neon Free is suitable for a demo, not a production availability guarantee. Keep separate backups of anything you cannot recreate.

## Redeploying changes

Push a new commit to the connected branch; Render automatically rebuilds the frontend and backend. For a manual redeploy, open each Render service and choose **Manual Deploy → Deploy latest commit**. A change to `VITE_API_BASE_URL` requires a new frontend build. Database schema changes are applied by the backend start command on deployment.

## Useful URLs after deployment

- Frontend: `https://iq-ai-frontend.onrender.com`
- Backend health: `https://iq-ai-api.onrender.com/health`
- Backend API docs: `https://iq-ai-api.onrender.com/docs`

Use the actual hostnames shown in Render if they differ from these defaults.
