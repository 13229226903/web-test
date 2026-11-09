# 守护：持续把 MCP 自己的 Chrome 窗口钉在屏幕外，避免上传/导航时置顶用户桌面。
# 只处理 --user-data-dir 含 mcp-profile 的 chrome 进程树，不碰用户自己的浏览器。
Add-Type @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class McpGuard {
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr l);
  public delegate bool EnumWindowsProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
  public static List<IntPtr> Find(uint[] pids){
    var set=new HashSet<uint>(pids); var res=new List<IntPtr>();
    EnumWindows((h,l)=>{ uint p=0; GetWindowThreadProcessId(h,out p);
      if(set.Contains(p) && IsWindowVisible(h)) res.Add(h); return true; }, IntPtr.Zero);
    return res;
  }
}
"@
$SWP_NOACTIVATE=0x0010; $SWP_NOSIZE=0x0001; $SWP_NOMOVE=0x0002; $SWP_NOZORDER=0x0004
while($true){
  $all = Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -match 'mcp-profile' }
  if ($all) {
    $roots = $all | Where-Object { $_.CommandLine -notmatch '--type=' } | Select-Object -ExpandProperty ProcessId
    $tree = New-Object System.Collections.Generic.HashSet[int]
    foreach($r in $roots){ [void]$tree.Add([int]$r) }
    $ch=$true
    while($ch){ $ch=$false; foreach($p in $all){ if($p.ParentProcessId -and $tree.Contains([int]$p.ParentProcessId) -and -not $tree.Contains([int]$p.ProcessId)){ [void]$tree.Add([int]$p.ProcessId); $ch=$true } } }
    $pids = [uint32[]]($tree | ForEach-Object { [uint32]$_ })
    foreach($h in [McpGuard]::Find($pids)){ [McpGuard]::SetWindowPos($h,[IntPtr]::Zero,-32000,-32000,0,0,($SWP_NOACTIVATE -bor $SWP_NOSIZE)) | Out-Null }
  }
  Start-Sleep -Milliseconds 400
}
