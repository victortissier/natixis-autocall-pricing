import numpy as np
import time

#Paramètres
T = 8 #Maturité
n_assets = 4 #Nb actifs du panier
n_obs = T * 4 #Nb observations (trimestrielles)
dt = 0.25 #Période entre chaque observation
nb_simul = 10000
r = 0.02 #Taux sans risque
div = 0.03 #Rendement du dividende
S0 = 100 #Niveau initial des actifs
vols = np.array([0.20, 0.22, 0.18, 0.25]) #Volatilité

#Matrice de corrélation
rho = 0.3
corr_matrix = np.full((n_assets, n_assets), rho)
np.fill_diagonal(corr_matrix, 1.0)
#Décomposition Cholesky
L = np.linalg.cholesky(corr_matrix)

#Simulation des scénarios
np.random.seed(int(time.time())) #Graine aléatoire
S = np.zeros((nb_simul, n_obs + 1, n_assets)) #Ensemble des simulations pour chaque actif et chaque simulation
S[:, 0, :] = S0 #Au 1er trimestre, chaque actif vaut 100

for t in range(1, n_obs + 1):
    Z = np.random.normal(size=(nb_simul, n_assets)) #Bruit gaussien
    Z_corr = Z @ L.T #Corrélation entre actifs
    drift = (r - div - 0.5 * vols**2) * dt
    diffusion = vols * np.sqrt(dt) * Z_corr
    S[:, t, :] = S[:, t-1, :] * np.exp(drift + diffusion) #Maj des prix

basket = np.mean(S, axis=2) #Moy des 4 actifs pour chaque simul et chaque observation

#Graphique simulations des trajectoires
import matplotlib.pyplot as plt
n_plot = 30
time_grid = np.linspace(0, T, n_obs + 1)
plt.figure(figsize=(12, 6))
for i in range(n_plot):
    plt.plot(time_grid, basket[i], lw=0.8, alpha=0.6)
plt.axhline(100, color='green', linestyle='--', label='Niveau Initial (100%)')
plt.axhline(60, color='red', linestyle='--', label='Barrière (60%)')
plt.title("Échantillon de trajectoires du panier simulé", color='#581D74', fontweight='bold')
plt.xlabel("Temps (en années)")
plt.ylabel("Valeur du panier")
plt.legend()
plt.grid(True)
plt.show()

gain_par_trim = 0.01525 #Gain par trimestre si autocall
gain_final = 0.488 #Gain à maturité si panier >= 100%
barriere = 0.60 #Seuil de protection
valeur_nominale = 1000
discount_factor = np.exp(-r * T)

payoffs = np.zeros(nb_simul) #Initialisation des gains pour chaque simul
maturities = np.full(nb_simul, T, dtype=np.float64) #Stocke la date de remboursement pour chaque simul

for i in range(5, n_obs+1): #observations du trimestre 5 à 32
    autocall = basket[:, i] >= 100
    not_already_called = payoffs == 0
    triggered = autocall & not_already_called
    payoffs[triggered] = valeur_nominale * (1 + gain_par_trim * i)
    maturities[triggered] = i * dt

final_vals = basket[:, -1]
non_called = payoffs == 0

#Scénario favorable
scenario1 = (final_vals >= 100) & non_called
payoffs[scenario1] = valeur_nominale * (1 + gain_final)

#Scénario neutre
scenario2 = (final_vals >= 60) & (final_vals < 100) & non_called
payoffs[scenario2] = valeur_nominale

#Scénario défavorable
scenario3 = (final_vals < 60) & non_called
payoffs[scenario3] = valeur_nominale * final_vals[scenario3] / 100

#Actualisation des payoffs
actualised = payoffs * np.exp(-r * maturities)
#Estimation par simulation de Monte Carlo
price_estimate = np.mean(actualised)

#Graphique Distribution des payoffs actualisés
plt.figure(figsize=(12, 6))
n, bins, patches = plt.hist(actualised, bins=63, color='#581D74', edgecolor='black', zorder=2)
for i in range(len(n)):
    if n[i] > 0:  # éviter d’étiqueter les barres vides
        bin_center = (bins[i] + bins[i+1]) / 2
        plt.text(bin_center, n[i], str(int(n[i])), ha='center', va='bottom', fontsize=8, rotation=90)
plt.axvline(float(price_estimate), color='red', linestyle='--', label=f'Prix estimé ≈ {price_estimate:.2f} €')
plt.title("Distribution des payoffs actualisés", color='#581D74', fontweight='bold')
plt.xlabel("Payoff actualisé (€)")
plt.ylabel("Fréquence")
plt.legend()
plt.grid(True, zorder = 0)
plt.show()

prix_emission = 1000
marge_implicite = (prix_emission - float(price_estimate)) / prix_emission * 100

print(f"Prix simulé du produit structuré : {price_estimate:.2f} €")
print(f"Marge implicite estimée         : {marge_implicite:.2f} %")

#Vérification de la cohérence des résultats
print("Payoff actualisé maximal =", np.max(actualised))
print(f"Maturité associée au payoff actualisé maximal : {maturities[np.argmax(actualised)]:.2f} ans")
nb_traj_sup_100 = np.sum(basket[:, 5] >= 100)
print(f"Nombre de trajectoires ≥ 100 au 5e trimestre (t = {5 * dt:.2f} ans) : {nb_traj_sup_100}")