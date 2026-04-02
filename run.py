from app import create_app

app = create_app()

if __name__ == "__main__":
    print("[*] Démarrage du serveur Flask MVP sur le port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
