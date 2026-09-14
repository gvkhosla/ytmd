class Ytmd < Formula
  desc "Use YouTube videos with your agent: local captions and timestamped evidence"
  homepage "https://gvkhosla.github.io/ytmd/"
  url "https://github.com/gvkhosla/ytmd.git", tag: "v0.7.0"
  license "MIT"
  head "https://github.com/gvkhosla/ytmd.git", branch: "main"

  depends_on "python@3"
  depends_on "yt-dlp"

  def install
    libexec.install "ytmd", "SKILL.md", "LICENSE", "install.sh"
    chmod 0755, libexec/"ytmd"
    bin.install_symlink libexec/"ytmd"
  end

  def caveats
    <<~EOS
      This installs the CLI. yt-dlp is required at runtime.

      To install the Pi/Codex/Claude Code skill from this copy:
        ytmd skill --agent all

      Restart your coding agent after installing the skill.
      If `ytmd doctor` warns stale_path_copy, an older installer is ahead of Homebrew on PATH.
    EOS
  end

  test do
    assert_match "ytmd", shell_output("#{bin}/ytmd --version")
  end
end
