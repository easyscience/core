module.exports = async ({ github, context, core }) => {
  // Repo context
  const owner = context.repo.owner
  const repo = context.repo.repo

  // Link to the exact workflow run that detected the conflict
  const runUrl = `${context.serverUrl}/${owner}/${repo}/actions/runs/${context.runId}`

  // We use a *stable title* so we can find/reuse the same "conflict tracker" issue
  // instead of creating a new issue on every failed run.
  const title = 'Backmerge conflict: master → develop'

  // Comment/issue body includes the run URL so maintainers can jump straight to logs.
  const body = [
    'Automatic backmerge failed due to merge conflicts.',
    '',
    `Workflow run: ${runUrl}`,
    '',
    'Manual resolution required.',
  ].join('\n')

  // Label applied to the tracker issue (assumed to already exist in the repo).
  const label = '[bot] backmerge'

  // Search issues by title across *open and closed* issues.
  // Why: if the conflict was resolved previously and the issue was closed,
  // we prefer to reopen it and append a new comment instead of creating duplicates.
  const q = `repo:${owner}/${repo} is:issue in:title "${title}"`
  const search = await github.rest.search.issuesAndPullRequests({
    q,
    per_page: 10,
  })

  // Pick the first exact-title match (search can return partial matches).
  const existing = search.data.items.find((i) => i.title === title)

  if (existing) {
    // If a tracker issue exists, reuse it:
    // - reopen it if needed
    // - add a comment with the new run URL
    if (existing.state === 'closed') {
      await github.rest.issues.update({
        owner,
        repo,
        issue_number: existing.number,
        state: 'open',
      })
    }

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: existing.number,
      body,
    })

    core.notice(`Conflict issue updated: #${existing.number}`)
    return
  }

  // No tracker issue exists yet -> create the first one.
  await github.rest.issues.create({
    owner,
    repo,
    title,
    body,
    labels: [label],
  })
}
