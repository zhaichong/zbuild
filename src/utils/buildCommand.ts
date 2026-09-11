export const WEB_FRONTEND_PROJECT = 'yarward-web-frontend'
export const WEB_FRONTEND_MICRO_MIN_VERSION = [3, 4, 4] as const
export const WEB_FRONTEND_MICRO_COMMAND = 'deploy-micro.sh'

type VersionTriple = readonly [number, number, number]

export function parseBranchVersion(branch: string): [number, number, number] | null {
  const match = String(branch || '').trim().match(/^(\d+)\.(\d+)(?:\.(\d+))?/)
  if (!match) return null
  return [Number(match[1]), Number(match[2]), Number(match[3] || 0)]
}

function versionGte(actual: VersionTriple, minimum: VersionTriple): boolean {
  for (let i = 0; i < 3; i += 1) {
    if (actual[i] > minimum[i]) return true
    if (actual[i] < minimum[i]) return false
  }
  return true
}

export function projectBasename(projectName: string): string {
  const parts = String(projectName || '').replace(/\\/g, '/').split('/')
  return (parts[parts.length - 1] || '').toLowerCase()
}

export function isWebFrontendProject(projectName: string): boolean {
  return projectBasename(projectName) === WEB_FRONTEND_PROJECT
}

export function branchMeetsMicroVersion(branch: string): boolean {
  const version = parseBranchVersion(branch)
  return version !== null && versionGte(version, WEB_FRONTEND_MICRO_MIN_VERSION)
}

export function isWebFrontendMicroBranch(projectName: string, branch = ''): boolean {
  return isWebFrontendProject(projectName) && branchMeetsMicroVersion(branch)
}

export function resolveEffectiveBuildCommand(
  projectName: string,
  branch: string,
  options: {
    branchCommands?: Record<string, string>
    projectCommand?: string
    globalCommand?: string
  } = {},
): string {
  const fallback = options.projectCommand || options.globalCommand || 'deploy.sh'
  if (isWebFrontendProject(projectName)) {
    return branchMeetsMicroVersion(branch) ? WEB_FRONTEND_MICRO_COMMAND : fallback
  }

  const branchCmds = options.branchCommands
  if (branchCmds && branch) {
    if (branchCmds[branch]) return branchCmds[branch]
    for (const [pattern, cmd] of Object.entries(branchCmds)) {
      if (pattern.endsWith('*')) {
        const prefix = pattern.slice(0, -1)
        if (branch.startsWith(prefix)) return cmd
      }
    }
  }
  return fallback
}
