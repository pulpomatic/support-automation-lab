"""
Class: Terminal

This class is responsible for managing the terminal interface.
"""
class Terminal:
    
    def get_logo():
        return r"""
                        _,--._
                      ,'      `.
              |\     / ,-.  ,-. \     /|
              )o),/ ( ( o )( o ) ) \.(o(
             /o/// /|  `-'  `-'  |\ \\\o\
            / / |\ \(   .    ,   )/ /| \ \
            | | \o`-/    `\/'    \-'o/ | |
            \ \  `,'              `.'  / /
         \.  \ `-'  ,'|   /\   |`.  `-' /  ,/
          \`. `.__,' /   /  \   \ `.__,' ,'/
           \o\     ,'  ,'    `.  `.     /o/
            \o`---'  ,'        `.  `---'o/
             `.____,'            `.____,'

  _____                                        _         _    _       _                 _ 
 |  __ \                                      | |       | |  | |     | |               | |
 | |  | | ___   ___ _   _ _ __ ___   ___ _ __ | |_ ___  | |  | |_ __ | | ___   __ _  __| |
 | |  | |/ _ \ / __| | | | '_ ` _ \ / _ | '_ \| __/ __| | |  | | '_ \| |/ _ \ / _` |/ _` |
 | |__| | (_) | (__| |_| | | | | | |  __| | | | |_\__ \ | |__| | |_) | | (_) | (_| | (_| |
 |_____/ \___/ \___|\__,_|_| |_| |_|\___|_| |_|\__|___/  \____/| .__/|_|\___/ \__,_|\__,_|
                                                               | |                        
                                                               |_|                        

             """

    def account_name():
        account_name = input("Ingresa el nombre de la cuenta o su legacy_code: ")
        return account_name

    def account_core_id():
        core_id = input("Ingresa el core_id de la cuenta: ")
        return core_id

# Llamar a los métodos y almacenar los resultados
nombre_cuenta = Terminal.account_name()
core_id = Terminal.account_core_id()

# Imprimir los resultados
print(f"Nombre de la cuenta o legacy_code: {nombre_cuenta}")
print(f"Core ID de la cuenta: {core_id}")