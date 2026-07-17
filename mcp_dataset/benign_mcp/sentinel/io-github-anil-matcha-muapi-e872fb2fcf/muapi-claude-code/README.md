# MuAPI – Claude Code Plugin

A Claude Code plugin that gives Claude the power to generate images, create videos, edit visuals, and more — all powered by [MuAPI](https://muapi.com).

Simply install the plugin and start asking Claude to generate media for you.

## ✨ What It Can Do

| Tool | Description |
|------|-------------|
| `generate_image` | Generate images from text prompts |
| `generate_video` | Generate videos from text prompts |
| `edit_image` | Edit an existing image with instructions |
| `image_to_video` | Convert a still image into a video |
| `upload_file` | Upload files to MuAPI for processing |
| `list_models` | Browse available model categories |
| `model_details` | Get details about a specific model |
| `get_prediction` | Track the status of an async prediction |
| `account_balance` | Check your MuAPI account balance |

## 🚀 Installation

### Install as a Claude Code Plugin

```bash
claude plugin add muapi
```

Or install directly from GitHub:

```bash
claude plugin add https://github.com/SamurAIGPT/muapi-claude-code.git
```

### Configure Your API Key

Set your MuAPI API key:

```bash
claude config set plugins.muapi.env.MUAPI_API_KEY your_api_key_here
```

Get your API key from [muapi.com](https://muapi.com).

## 💡 Usage

Once installed, just ask Claude naturally:

**Image Generation**
```
Generate an image of a futuristic city at sunset
```

**Video Generation**
```
Generate a cinematic drone shot over mountains
```

**Image Editing**
```
Edit this image to add a rainbow in the sky
```

**Image to Video**
```
Convert this image into a slow zoom-in video
```

## 🔧 Slash Commands

After installing, you can invoke skills directly:

| Command | What it does |
|---------|-------------|
| `/muapi:generate-image <prompt>` | Generate an image from a text prompt |
| `/muapi:generate-video <prompt>` | Generate a video from a text prompt |
| `/muapi:edit-image <instructions>` | Edit an existing image |
| `/muapi:image-to-video <image url>` | Animate a still image into a video |
| `/muapi:media-help` | Explore available models and get recommendations |

## 🛠 Development

If you want to run the plugin locally for development:

```bash
git clone https://github.com/SamurAIGPT/muapi-claude-code.git
cd muapi-claude-code
npm install
```

Create a `.env` file:

```env
MUAPI_API_KEY=your_api_key_here
```

Run the MCP server directly:

```bash
node src/index.js
```

## 📁 Project Structure

```
muapi-claude-code/
├── .claude-plugin/
│   └── plugin.json            # Claude Code plugin manifest
├── src/
│   ├── index.js               # MCP server entry point
│   └── tools/
│       ├── generateImage.js   # Image generation
│       ├── generateVideo.js   # Video generation
│       ├── editImage.js       # Image editing
│       ├── imageToVideo.js    # Image-to-video conversion
│       ├── uploadFile.js      # File upload
│       ├── listModels.js      # Model listing
│       ├── modelDetails.js    # Model details
│       ├── getPrediction.js   # Prediction tracking
│       └── accountBalance.js  # Account balance
├── .mcp.json                  # MCP server config
├── package.json
└── .env                       # API key (not committed)
```

## 📄 License

ISC
