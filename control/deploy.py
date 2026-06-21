import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import os
import sys
import threading
from datetime import datetime


class DeployTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LifeOS Deploy Tool")
        self.geometry("800x460")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.root_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.dev_dir    = os.path.join(self.root_dir, "dev")
        self.prod_dir   = os.path.join(self.root_dir, "prod")
        self._stop_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy.stop")

        self.create_widgets()
        self.after(150, self._post_init)
        self.after(1000, self._check_stop_file)

    # ── Startup ───────────────────────────────────────────────────────────────

    def _post_init(self):
        self.initialize_worktree()
        self.refresh_commits()

    def _check_stop_file(self):
        if os.path.exists(self._stop_file):
            try:
                os.remove(self._stop_file)
            except OSError:
                pass
            self.on_close()
            return
        self.after(1000, self._check_stop_file)

    # ── Worktree init ─────────────────────────────────────────────────────────

    def initialize_worktree(self):
        _, _, rc = self._git(["rev-parse", "--git-dir"])
        if rc != 0:
            self._log("ERROR: dev/ is not a git repository. Run 'git init' inside dev/ first.")
            self.deploy_btn.config(state=tk.DISABLED)
            self.commit_btn.config(state=tk.DISABLED)
            self.refresh_btn.config(state=tk.DISABLED)
            return

        stdout, _, _ = self._git(["worktree", "list", "--porcelain"])
        prod_norm  = os.path.normcase(os.path.normpath(self.prod_dir))
        registered = any(
            line.startswith("worktree ") and
            os.path.normcase(os.path.normpath(line[9:])) == prod_norm
            for line in stdout.splitlines()
        )

        if registered:
            self._log("Worktree OK — prod/ is already registered.")
        else:
            self._log("Worktree not found — creating prod/ as a detached worktree...")
            if os.path.isdir(self.prod_dir) and os.listdir(self.prod_dir):
                self._log(
                    "WARNING: prod/ exists as a non-empty directory. "
                    "Remove it manually if creation fails."
                )
            out, err, rc = self._git(["worktree", "add", "--detach", self.prod_dir, "HEAD"])
            if rc == 0:
                self._log(f"Worktree created. {out or ''}")
            else:
                self._log(f"ERROR creating worktree: {err}")

    # ── Git helpers ───────────────────────────────────────────────────────────

    def _git(self, args, cwd=None):
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or self.dev_dir,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def _update_highlights(self):
        dev_hash, _, rc = self._git(["rev-parse", "HEAD"])
        dev_hash = dev_hash if rc == 0 else None

        if os.path.isdir(self.prod_dir):
            prod_hash, _, rc = self._git(["rev-parse", "HEAD"], cwd=self.prod_dir)
            prod_hash = prod_hash if rc == 0 else None
        else:
            prod_hash = None

        for iid in self.commit_tree.get_children():
            tags    = self.commit_tree.item(iid, "tags")
            full    = tags[0] if tags else ""
            is_dev  = bool(dev_hash  and dev_hash.startswith(full[:7]))
            is_prod = bool(prod_hash and prod_hash.startswith(full[:7]))

            new_tags = [full]
            if is_prod:
                new_tags.append("deployed")   # green — prod is here
            elif is_dev:
                new_tags.append("dev_head")   # blue — dev HEAD, not yet deployed

            self.commit_tree.item(iid, tags=tuple(new_tags))

    # ── Commit list ───────────────────────────────────────────────────────────

    def refresh_commits(self):
        self.commit_tree.delete(*self.commit_tree.get_children())
        stdout, stderr, rc = self._git([
            "log", "--pretty=format:%H|%ad|%s",
            "--date=format:%Y-%m-%d %H:%M",
        ])
        if rc != 0:
            self._log(f"git log failed: {stderr}")
            return
        for line in stdout.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                full_hash, date, message = parts
                self.commit_tree.insert(
                    "", tk.END,
                    values=(full_hash[:8], date, message),
                    tags=(full_hash,),
                )
        self._update_highlights()
        self._log("Commit list refreshed.")

    # ── Commit from dev/ ──────────────────────────────────────────────────────

    def commit_from_dev(self):
        status_out, _, _ = self._git(["status", "--porcelain"])
        if not status_out.strip():
            messagebox.showinfo("Nothing to Commit", "Working tree is clean — no changes to commit.")
            return

        message = simpledialog.askstring("Commit Message", "Enter commit message:", parent=self)
        if not message or not message.strip():
            return

        threading.Thread(target=self._do_commit, args=(message.strip(),), daemon=True).start()

    def _do_commit(self, message):
        self.after(0, lambda: self.commit_btn.config(state=tk.DISABLED))
        self.after(0, lambda: self.deploy_btn.config(state=tk.DISABLED))
        self._log(f"Staging all changes in dev/...")

        _, stderr, rc = self._git(["add", "-A"])
        if rc != 0:
            self._log(f"ERROR: git add failed — {stderr}")
            self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))
            return

        self._log(f"Committing: {message}")
        _, stderr, rc = self._git(["commit", "-m", message])
        if rc != 0:
            self._log(f"ERROR: git commit failed — {stderr}")
            self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))
            return

        new_hash, _, rc = self._git(["rev-parse", "HEAD"])
        if rc != 0:
            self._log("ERROR: could not resolve new HEAD after commit.")
            self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))
            return

        short = new_hash[:8]
        self._log(f"Commit created ({short}). Deploying to prod/...")

        _, stderr, rc = self._git(["checkout", new_hash], cwd=self.prod_dir)
        if rc != 0:
            self._log(f"ERROR: checkout failed — {stderr}")
            self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))
            return

        self._log(f"Done — dev/ and prod/ are now at {short}.")
        self.after(0, self.refresh_commits)
        self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
        self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))

    # ── Deploy selected commit ────────────────────────────────────────────────

    def deploy_selected(self):
        sel = self.commit_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a commit to deploy.")
            return
        item      = self.commit_tree.item(sel[0])
        full_hash = self.commit_tree.item(sel[0], "tags")[0]
        short     = item["values"][0]
        message   = item["values"][2]

        if not messagebox.askyesno("Confirm Deploy", f"Deploy commit {short}?\n\n{message}"):
            return

        threading.Thread(target=self._do_deploy, args=(full_hash, short), daemon=True).start()

    def _do_deploy(self, full_hash, short_hash):
        self.after(0, lambda: self.deploy_btn.config(state=tk.DISABLED))
        self.after(0, lambda: self.commit_btn.config(state=tk.DISABLED))
        self._log(f"Deploying {short_hash} to prod/...")

        _, stderr, rc = self._git(["checkout", full_hash], cwd=self.prod_dir)
        if rc != 0:
            self._log(f"ERROR: checkout failed — {stderr}")
            self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))
            self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
            return

        self.after(0, self._update_highlights)
        self.after(0, lambda: self.deploy_btn.config(state=tk.NORMAL))
        self.after(0, lambda: self.commit_btn.config(state=tk.NORMAL))
        self._log(f"Deploy complete -> {short_hash}")

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, text):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {text}", flush=True)

    # ── UI ────────────────────────────────────────────────────────────────────

    def create_widgets(self):
        content = ttk.Frame(self, padding=10)
        content.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content, text="Commit History  (dev/)", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 4))

        tree_frame = ttk.Frame(content)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("hash", "date", "message")
        self.commit_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self.commit_tree.heading("hash",    text="Hash")
        self.commit_tree.heading("date",    text="Date & Time")
        self.commit_tree.heading("message", text="Commit Message")
        self.commit_tree.column("hash",    width=65,  stretch=False, anchor=tk.CENTER)
        self.commit_tree.column("date",    width=135, stretch=False)
        self.commit_tree.column("message", width=500)
        self.commit_tree.tag_configure("deployed", background="#1e3a2f", foreground="#4ec9b0")  # green  — prod HEAD
        self.commit_tree.tag_configure("dev_head", background="#1a2a3a", foreground="#569cd6")  # blue   — dev HEAD (undeployed)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.commit_tree.yview)
        self.commit_tree.configure(yscrollcommand=vsb.set)
        self.commit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_row = ttk.Frame(content)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        self.commit_btn = ttk.Button(btn_row, text="✚  Commit From dev/", command=self.commit_from_dev)
        self.commit_btn.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Separator(btn_row, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        self.deploy_btn = ttk.Button(btn_row, text="🚀  Deploy Selected", command=self.deploy_selected)
        self.deploy_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.refresh_btn = ttk.Button(btn_row, text="↻  Refresh", command=self.refresh_commits)
        self.refresh_btn.pack(side=tk.LEFT)

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def on_close(self):
        self.destroy()


if __name__ == "__main__":
    app = DeployTool()
    app.mainloop()
