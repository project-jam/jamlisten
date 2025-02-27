import {
  ChatInputCommandInteraction,
  SlashCommandBuilder,
  EmbedBuilder,
  AttachmentBuilder,
} from "discord.js";
import type { Command } from "../../types/Command";
import { Logger } from "../../utils/logger";

export const command: Command = {
  data: new SlashCommandBuilder()
    .setName("topographic")
    .setDescription("Generate topographic-related images")
    .addSubcommand((subcommand) =>
      subcommand
        .setName("lines")
        .setDescription("Generate topographic lines image")
        .addNumberOption((option) =>
          option
            .setName("width")
            .setDescription("Width of the image (100-3840)")
            .setMinValue(100)
            .setMaxValue(3840)
            .setRequired(false),
        )
        .addNumberOption((option) =>
          option
            .setName("height")
            .setDescription("Height of the image (100-2160)")
            .setMinValue(100)
            .setMaxValue(2160)
            .setRequired(false),
        )
        .addNumberOption((option) =>
          option
            .setName("thickness")
            .setDescription("Thickness of the lines (1-10)")
            .setMinValue(1)
            .setMaxValue(10)
            .setRequired(false),
        )
        .addStringOption((option) =>
          option
            .setName("linecolor")
            .setDescription("Line color in hex (e.g., FFFFFF for white)")
            .setRequired(false)
            .setMinLength(6)
            .setMaxLength(6),
        )
        .addStringOption((option) =>
          option
            .setName("bgcolor")
            .setDescription("Background color in hex (e.g., 000000 for black)")
            .setRequired(false)
            .setMinLength(6)
            .setMaxLength(6),
        ),
    )
    .addSubcommand((subcommand) =>
      subcommand
        .setName("wavy")
        .setDescription("Generate wavy topographic lines image")
        .addNumberOption((option) =>
          option
            .setName("width")
            .setDescription("Width of the image (100-3840)")
            .setMinValue(100)
            .setMaxValue(3840)
            .setRequired(false),
        )
        .addNumberOption((option) =>
          option
            .setName("height")
            .setDescription("Height of the image (100-2160)")
            .setMinValue(100)
            .setMaxValue(2160)
            .setRequired(false),
        )
        .addStringOption((option) =>
          option
            .setName("linecolor")
            .setDescription("Line color in hex (e.g., FFFFFF for white)")
            .setRequired(false)
            .setMinLength(6)
            .setMaxLength(6),
        )
        .addStringOption((option) =>
          option
            .setName("bgcolor")
            .setDescription("Background color in hex (e.g., 000000 for black)")
            .setRequired(false)
            .setMinLength(6)
            .setMaxLength(6),
        ),
    ),

  async execute(interaction: ChatInputCommandInteraction) {
    const subcommand = interaction.options.getSubcommand();

    switch (subcommand) {
      case "lines":
        await handleTopographicLines(interaction);
        break;
      case "wavy":
        await handleTopographicWavy(interaction);
        break;
      default:
        await interaction.reply({
          content: "Unknown subcommand",
          ephemeral: true,
        });
    }
  },
};

async function handleTopographicLines(
  interaction: ChatInputCommandInteraction,
) {
  await interaction.deferReply();

  try {
    // Get options with defaults
    const width = interaction.options.getNumber("width") || 1920;
    const height = interaction.options.getNumber("height") || 1080;
    const thickness = interaction.options.getNumber("thickness") || 3;
    const lineColor = interaction.options.getString("linecolor") || "FFFFFF";
    const bgColor = interaction.options.getString("bgcolor") || "000000";

    // Validate hex colors
    const hexColorRegex = /^[0-9A-Fa-f]{6}$/;
    if (!hexColorRegex.test(lineColor) || !hexColorRegex.test(bgColor)) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor("#ff3838")
            .setDescription(
              "❌ Invalid hex color format. Use format like 'FFFFFF' for white.",
            ),
        ],
      });
      return;
    }

    // Construct API URL
    const apiUrl = `https://api.project-jam.is-a.dev/api/v0/image/topographic-lines?width=${width}&height=${height}&thickness=${thickness}&lineColor=${lineColor}&bgColor=${bgColor}`;

    // Fetch the image
    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }

    // Convert to buffer
    const imageBuffer = Buffer.from(await response.arrayBuffer());

    // Create attachment
    const attachment = new AttachmentBuilder(imageBuffer, {
      name: "topographic-lines.png",
    });

    // Create embed
    const embed = new EmbedBuilder()
      .setColor(`#${lineColor}`)
      .setTitle("🗺️ Topographic Lines Generated")
      .addFields(
        {
          name: "Dimensions",
          value: `${width}x${height}`,
          inline: true,
        },
        {
          name: "Line Thickness",
          value: thickness.toString(),
          inline: true,
        },
        {
          name: "Colors",
          value: `Lines: #${lineColor}\nBackground: #${bgColor}`,
          inline: true,
        },
      )
      .setImage("attachment://topographic-lines.png")
      .setTimestamp()
      .setFooter({
        text: `Requested by ${interaction.user.tag}`,
        iconURL: interaction.user.displayAvatarURL(),
      });

    await interaction.editReply({
      embeds: [embed],
      files: [attachment],
    });
  } catch (error) {
    Logger.error("Topographic lines command failed:", error);
    await interaction.editReply({
      embeds: [
        new EmbedBuilder()
          .setColor("#ff3838")
          .setDescription(
            "❌ Failed to generate topographic lines. Please try again later.",
          ),
      ],
    });
  }
}

async function handleTopographicWavy(interaction: ChatInputCommandInteraction) {
  await interaction.deferReply();

  try {
    // Get options with defaults (wavy doesn't use thickness)
    const width = interaction.options.getNumber("width") || 1920;
    const height = interaction.options.getNumber("height") || 1080;
    const lineColor = interaction.options.getString("linecolor") || "FFFFFF";
    const bgColor = interaction.options.getString("bgcolor") || "000000";

    // Validate hex colors
    const hexColorRegex = /^[0-9A-Fa-f]{6}$/;
    if (!hexColorRegex.test(lineColor) || !hexColorRegex.test(bgColor)) {
      await interaction.editReply({
        embeds: [
          new EmbedBuilder()
            .setColor("#ff3838")
            .setDescription(
              "❌ Invalid hex color format. Use format like 'FFFFFF' for white.",
            ),
        ],
      });
      return;
    }

    // Construct API URL for wavy lines, adding wavy=true
    const apiUrl = `https://api.project-jam.is-a.dev/api/v0/image/topographic-lines?width=${width}&height=${height}&lineColor=${lineColor}&bgColor=${bgColor}&wavy=true`;

    // Fetch the image
    const response = await fetch(apiUrl);
    if (!response.ok) {
      throw new Error(`API returned status ${response.status}`);
    }

    // Convert to buffer
    const imageBuffer = Buffer.from(await response.arrayBuffer());

    // Create attachment
    const attachment = new AttachmentBuilder(imageBuffer, {
      name: "topographic-wavy-lines.png",
    });

    // Create embed for wavy lines
    const embed = new EmbedBuilder()
      .setColor(`#${lineColor}`)
      .setTitle("🌊 Wavy Topographic Lines Generated") // Updated title
      .addFields(
        {
          name: "Dimensions",
          value: `${width}x${height}`,
          inline: true,
        },
        {
          name: "Colors",
          value: `Lines: #${lineColor}\nBackground: #${bgColor}`,
          inline: true,
        },
      )
      .setImage("attachment://topographic-wavy-lines.png") // Updated filename
      .setTimestamp()
      .setFooter({
        text: `Requested by ${interaction.user.tag}`,
        iconURL: interaction.user.displayAvatarURL(),
      });

    await interaction.editReply({
      embeds: [embed],
      files: [attachment],
    });
  } catch (error) {
    Logger.error("Topographic wavy lines command failed:", error);
    await interaction.editReply({
      embeds: [
        new EmbedBuilder()
          .setColor("#ff3838")
          .setDescription(
            "❌ Failed to generate wavy topographic lines. Please try again later.",
          ),
      ],
    });
  }
}
