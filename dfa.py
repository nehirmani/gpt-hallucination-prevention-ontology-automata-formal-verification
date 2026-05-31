# DFA (Deterministik Sonlu Otomat) Sinifi
# Bicimsel Diller ve Otomatlar dersi - Grup B, Proje 2
# Nobel odulu dogrulama karari icin kullanilir

class DFA:
    def __init__(self):
        # 5-demet tanimi: (Q, Sigma, delta, q0, F)
        self.Q = {'q_start', 'q_verified', 'q_suspicious', 'q_rejected'}
        self.Sigma = {'tam_esleme', 'kismi_esleme', 'esleme_yok'}
        self.q0 = 'q_start'
        self.F = {'q_verified'}
        self.delta = {
            ('q_start', 'tam_esleme'): 'q_verified',
            ('q_start', 'kismi_esleme'): 'q_suspicious',
            ('q_start', 'esleme_yok'): 'q_rejected',
        }
        self.mevcut_durum = self.q0

    def gecis(self, giris_sembolu):
        """Gecis fonksiyonu: mevcut durum + giris -> yeni durum"""
        anahtar = (self.mevcut_durum, giris_sembolu)
        if anahtar in self.delta:
            self.mevcut_durum = self.delta[anahtar]
        else:
            self.mevcut_durum = 'q_rejected'
        return self.mevcut_durum

    def calistir(self, sinyal):
        """Baslangic durumundan baslatip tek sinyalle sonuc uret"""
        self.mevcut_durum = self.q0
        return self.gecis(sinyal)

    def kabul_ediyor_mu(self):
        """Mevcut durum kabul durumunda mi?"""
        return self.mevcut_durum in self.F


if __name__ == "__main__":
    dfa = DFA()
    print("DFA Test Sonuclari:")
    print("tam_esleme   ->", dfa.calistir('tam_esleme'))
    print("kismi_esleme ->", dfa.calistir('kismi_esleme'))
    print("esleme_yok   ->", dfa.calistir('esleme_yok'))
