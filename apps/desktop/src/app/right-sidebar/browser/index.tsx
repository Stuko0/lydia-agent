import { useStore } from '@nanostores/react'
import { type FormEvent, useCallback, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Codicon } from '@/components/ui/codicon'
import { Input } from '@/components/ui/input'
import { useI18n } from '@/i18n'
import { openExternalLink } from '@/lib/external-link'
import { cn } from '@/lib/utils'
import { $panesFlipped } from '@/store/layout'

import {
  $browserTabs,
  closeBrowserTab,
  upsertBrowserTab,
  type BrowserTab,
} from '@/store/browser-tabs'
import { RightSidebarSectionHeader } from '../index'
import { SidebarPanelLabel } from '../../shell/sidebar-label'

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

/** Strip trailing slash + protocol prefix for compact display. */
function displayUrl(url: string): string {
  try {
    const u = new URL(url)
    return u.hostname + u.pathname.replace(/\/$/, '')
  } catch {
    return url
  }
}

function TabRow({ tab, onOpen, onClose }: { tab: BrowserTab; onOpen: (url: string) => void; onClose: (id: string) => void }) {
  const domain = (() => {
    try {
      return new URL(tab.url).hostname
    } catch {
      return tab.url
    }
  })()

  return (
    <div className="group flex items-start gap-2 rounded-md px-2 py-1.5 transition-colors hover:bg-(--ui-control-hover-background)">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <Codicon name="globe" size="0.75rem" className="shrink-0 text-(--ui-text-tertiary)" />
          <span className="truncate text-[0.77rem] font-medium leading-5 text-foreground">
            {tab.title || tab.url}
          </span>
        </div>
        <div className="mt-0.5 flex items-center gap-2">
          <span className="truncate text-[0.65rem] text-(--ui-text-tertiary)">{domain}</span>
          <span className="shrink-0 text-[0.6rem] text-(--ui-text-quaternary)">{formatTime(tab.lastActiveAt)}</span>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          aria-label="Open in browser"
          className="text-(--ui-text-tertiary) hover:text-foreground"
          onClick={() => onOpen(tab.url)}
          size="icon-xs"
          variant="ghost"
        >
          <Codicon name="link-external" size="0.8125rem" />
        </Button>
        <Button
          aria-label="Navigate"
          className="text-(--ui-text-tertiary) hover:text-foreground"
          onClick={() => onOpen(tab.url)}
          size="icon-xs"
          variant="ghost"
        >
          <Codicon name="arrow-right" size="0.8125rem" />
        </Button>
        <Button
          aria-label="Close tab"
          className="text-(--ui-text-tertiary) hover:text-foreground"
          onClick={() => onClose(tab.id)}
          size="icon-xs"
          variant="ghost"
        >
          <Codicon name="close" size="0.8125rem" />
        </Button>
      </div>
    </div>
  )
}

export function BrowserPane() {
  const tabs = useStore($browserTabs)
  const panesFlipped = useStore($panesFlipped)
  const { t } = useI18n()
  const [inputUrl, setInputUrl] = useState('')
  const inputRef = useRef<HTMLInputElement | null>(null)

  const handleSubmit = useCallback((e: FormEvent) => {
    e.preventDefault()
    let url = inputUrl.trim()
    if (!url) return
    // Auto-prepend https:// if missing
    if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(url)) {
      url = 'https://' + url
    }
    setInputUrl('')
    upsertBrowserTab(url, displayUrl(url))
    openExternalLink(url)
  }, [inputUrl])

  return (
    <aside
      aria-label="Browser tabs"
      className={cn(
        'before:pointer-events-none relative flex h-full w-full min-w-0 flex-col overflow-hidden border-(--ui-stroke-secondary) bg-(--ui-sidebar-surface-background) pt-(--titlebar-height) text-(--ui-text-tertiary)',
        panesFlipped
          ? 'border-r shadow-[inset_-0.0625rem_0_0_color-mix(in_srgb,white_18%,transparent)]'
          : 'border-l shadow-[inset_0.0625rem_0_0_color-mix(in_srgb,white_18%,transparent)]'
      )}
    >
      <RightSidebarSectionHeader>
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <SidebarPanelLabel>Browser Tabs</SidebarPanelLabel>
          {tabs.length > 0 && (
            <span className="rounded-full bg-(--ui-bg-tertiary) px-1.5 text-[0.6rem] font-medium tabular-nums text-(--ui-text-quaternary)">
              {tabs.length}
            </span>
          )}
        </div>
        {tabs.length > 0 && (
          <Button
            aria-label="Clear all tabs"
            className="text-(--ui-text-tertiary) hover:text-foreground"
            onClick={() => $browserTabs.set([])}
            size="icon-xs"
            title="Clear all"
            variant="ghost"
          >
            <Codicon name="clear-all" size="0.8125rem" />
          </Button>
        )}
      </RightSidebarSectionHeader>

      {/* URL input bar */}
      <form className="flex shrink-0 gap-1 px-2 pb-2" onSubmit={handleSubmit}>
        <Input
          className="min-w-0 flex-1 text-[0.77rem]"
          onChange={e => setInputUrl(e.target.value)}
          placeholder="Enter a URL…"
          ref={inputRef}
          type="text"
          value={inputUrl}
        />
        <Button
          className="shrink-0"
          disabled={!inputUrl.trim()}
          size="sm"
          title="Open URL"
          type="submit"
        >
          <Codicon name="arrow-right" size="0.8125rem" />
        </Button>
      </form>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
        {tabs.length === 0 ? (
          <div className="flex flex-1 items-center justify-center px-4">
            <SidebarPanelLabel className="pl-0 text-(--ui-text-quaternary)">
              No active browser tabs
            </SidebarPanelLabel>
          </div>
        ) : (
          <div className="flex flex-col gap-0.5 p-2">
            {tabs.map(tab => (
              <TabRow
                key={tab.id}
                tab={tab}
                onOpen={openExternalLink}
                onClose={closeBrowserTab}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
