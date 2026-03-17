export {}; // This makes the file a module
// services/downloader.ts

const url = Deno.args[0];
const folder = Deno.args[1];
const isAudio = Deno.args[2] === "true";
const ytdlpPath = Deno.args[3];
const ariaPath = Deno.args[4];

if (!url || !folder) {
  console.error("Missing required arguments");
  Deno.exit(1);
}


// 1. Build arguments for yt-dlp
const args = [
  url,
  "-P", folder,
  "--newline",
  "--progress",              // This is okay here (it's for yt-dlp)
  "--no-warnings",
  // Fix the aria2c arguments below:
  "--progress-template", "[download] %(progress._percent_str)s", 
  "--external-downloader-args", "aria2c:--summary-interval=1 --console-log-level=notice", 
  // ^^^ Removed --progress from the line above ^^^
  "--remote-components", "ejs:github",
  "--external-downloader", ariaPath,
];

if (isAudio) {
  args.push("-x", "--audio-format", "mp3");
}

try {
  // 2. Initialize the command
  const command = new Deno.Command(ytdlpPath, {
    args: args,
    stdout: "piped",
    stderr: "piped",
  });

  // 3. Spawn the process
  const process = command.spawn();

  // 4. THE FIX: Pipe yt-dlp output to Deno's output in real-time
  // This is what allows Python's readline() to actually "see" the progress
  process.stdout.pipeTo(Deno.stdout.writable, { preventClose: true });
  process.stderr.pipeTo(Deno.stderr.writable, { preventClose: true });

  // 5. Wait for completion
  const status = await process.status;
  
  if (status.success) {
    console.log("Download completed successfully");
    Deno.exit(0);
  } else {
    console.error(`Process exited with code: ${status.code}`);
    Deno.exit(status.code);
  }

} catch (error) {
  console.error(`Deno Error: ${error.message}`);
  Deno.exit(1);
}