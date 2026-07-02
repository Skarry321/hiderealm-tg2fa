package ru.hiderealm.command;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.entity.Player;
import org.bukkit.scheduler.BukkitRunnable;
import ru.hiderealm.HideRealmPlugin;

public class ChangePasswordCommand implements org.bukkit.command.CommandExecutor {

    private final HideRealmPlugin plugin;
    private static final Component PREFIX = Component.text()
            .append(Component.text("HideRealm ", NamedTextColor.GOLD))
            .append(Component.text(">> ", NamedTextColor.GRAY))
            .build();

    public ChangePasswordCommand(HideRealmPlugin plugin) {
        this.plugin = plugin;
    }

    @Override
    public boolean onCommand(org.bukkit.command.CommandSender sender, org.bukkit.command.Command command, String label, String[] args) {
        if (!(sender instanceof Player player)) {
            sender.sendMessage(Component.text("Only players can use this command."));
            return true;
        }

        if (args.length < 1) {
            player.sendMessage(PREFIX.append(
                    Component.text("Использование: /cp <новый_пароль>", NamedTextColor.WHITE)));
            return true;
        }

        String newPassword = args[0];
        String cmd = plugin.getConfig()
                .getString("password-change-command", "authme changepassword %player% %password%")
                .replace("%player%", player.getName())
                .replace("%password%", newPassword);

        String finalCmd = cmd;
        new BukkitRunnable() {
            @Override
            public void run() {
                boolean ok = plugin.getServer().dispatchCommand(
                        plugin.getServer().getConsoleSender(), finalCmd);
                if (ok) {
                    player.sendMessage(PREFIX.append(
                            Component.text("Пароль успешно изменен!", NamedTextColor.GREEN)));
                } else {
                    player.sendMessage(PREFIX.append(
                            Component.text("Ошибка при смене пароля.", NamedTextColor.RED)));
                }
            }
        }.runTask(plugin);

        return true;
    }
}
