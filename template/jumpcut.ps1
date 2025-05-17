# PowerShell script: jumpcut.ps1

# Activate the virtual environment
& "{{SCRIPT_ROOT}}\venv\Scripts\Activate.ps1"

function Do-JumpCutOnFile {
    param([string]$file)

    python "{{SCRIPT_ROOT}}\src\jumpcutter.py" `
        --input_file "$file" `
        --silent_speed 9999 `
        --frame_margin 3 `
        --keep_start 2 `
        --keep_end 2 `
        --use_hardware_acc 1 `
        --silent_threshold 0.005
}

function Do-JumpCutOnDir {
    param([string]$dir)

    $subfiles = Get-ChildItem -Path $dir -File
    foreach ($subfile in $subfiles) {
        Do-JumpCut $subfile.FullName
    }
}

function Do-JumpCut {
    param([string]$path)

    if (Test-Path $path -PathType Container) {
        Do-JumpCutOnDir $path
    } else {
        Do-JumpCutOnFile $path
    }
}

# Process each argument
foreach ($file in $args) {
    Write-Host "Process $file..."
    Do-JumpCut $file
}

# Deactivate the virtual environment
# Only necessary if you launched a new shell — otherwise, PowerShell just continues
# Optional: You could deactivate manually or use `deactivate` if you are using virtualenvwrapper