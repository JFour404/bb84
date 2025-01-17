from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

np.set_printoptions(linewidth=np.inf)

num_qubits = 32

def generate_alice_data(num_qubits):
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(2, size=num_qubits)
    return alice_bits, alice_bases

def prepare_qubits(alice_bits, alice_bases):
    circuits = []
    for i in range(num_qubits):
        qc = QuantumCircuit(1, 1)
        if alice_bits[i] == 1:
            qc.x(0)
        if alice_bases[i] == 1:
            qc.h(0)
        circuits.append(qc)
    return circuits

def eve_intercepts(circuits, num_qubits):
    eve_bases = np.random.randint(2, size=num_qubits)
    eve_tampered_circuits = []
    simulator = AerSimulator()

    for i, qc in enumerate(circuits):
        eve_basis = eve_bases[i]
        qc_copy = qc.copy()
        if eve_basis == 1:
            qc_copy.h(0)
        qc_copy.measure(0, 0)
        result = simulator.run(transpile(qc_copy, simulator)).result()
        counts = result.get_counts()
        measured_bit = int(max(counts, key=counts.get))

        eve_qc = QuantumCircuit(1, 1)
        if measured_bit == 1:
            eve_qc.x(0)
        if eve_basis == 1:
            eve_qc.h(0)
        eve_tampered_circuits.append(eve_qc)
    return eve_bases, eve_tampered_circuits

def bob_measures(circuits, num_qubits):
    bob_bases = np.random.randint(2, size=num_qubits)
    bob_bits = []
    simulator = AerSimulator()

    for i, qc in enumerate(circuits):
        if bob_bases[i] == 1:
            qc.h(0)
        qc.measure(0, 0)
        result = simulator.run(transpile(qc, simulator)).result()
        counts = result.get_counts()
        measured_bit = int(max(counts, key=counts.get))
        bob_bits.append(measured_bit)
    return bob_bases, bob_bits

def reconcile_bases(alice_bases, bob_bases, alice_bits, bob_bits):
    matching_bases = alice_bases == bob_bases
    shared_key_indices = np.where(matching_bases)[0]
    alice_shared_key = alice_bits[shared_key_indices]
    bob_shared_key = np.array(bob_bits)[shared_key_indices]
    return alice_shared_key, bob_shared_key

def check_correct_bases(alice_bases, bob_bases):
    return alice_bases == bob_bases

def format_correct_bases(correct_bases):
    return ['K' if base else ' ' for base in correct_bases]

def create_correct_bits(bob_bits, correct_bases):
    return [bit if correct else -1 for bit, correct in zip(bob_bits, correct_bases)]

def randomly_store_half(correct_bits):
    valid_indices = [i for i, bit in enumerate(correct_bits) if bit != -1]
    selected_indices = np.random.choice(valid_indices, len(valid_indices) // 2, replace=False)
    half_correct_bits = [-1] * len(correct_bits)
    for index in selected_indices:
        half_correct_bits[index] = correct_bits[index]
    return half_correct_bits

def confirm_by_alice(alice_bits, half_correct_bits):
    return ['T' if bit == alice_bits[i] else 'F' if bit != -1 else ' ' for i, bit in enumerate(half_correct_bits)]

def create_outcome(correct_bits, half_correct_bits):
    return [bit if half_correct_bits[i] == -1 else -1 for i, bit in enumerate(correct_bits)]

def calculate_eavesdropping_ratio(confirmed_by_alice):
    total_intercepted = confirmed_by_alice.count('F')
    return (total_intercepted / num_qubits) * 100

def collect_data(eavesdropping_enabled=True):
    data = {}
    # Step 1
    alice_bits, alice_bases = generate_alice_data(num_qubits)
    data['alice_bits'] = alice_bits
    data['alice_bases'] = alice_bases 
    
    circuits = prepare_qubits(alice_bits, alice_bases)
    
    if eavesdropping_enabled:
        eve_bases, eve_tampered_circuits = eve_intercepts(circuits, num_qubits)
        data['eve_bases'] = eve_bases
        circuits = eve_tampered_circuits
    else:
        data['eve_bases'] = None

    # Step 2
    bob_bases, bob_bits = bob_measures(circuits, num_qubits)
    data['bob_bases'] = bob_bases
    data['bob_bits'] = bob_bits

    # Step 3
    alice_shared_key, bob_shared_key = reconcile_bases(alice_bases, bob_bases, alice_bits, bob_bits)
    data['alice_shared_key'] = alice_shared_key
    data['bob_shared_key'] = bob_shared_key

    # Step 4
    correct_bases = check_correct_bases(alice_bases, bob_bases)
    
    data['correct_bases'] = format_correct_bases(correct_bases)
    data['correct_bits'] = create_correct_bits(bob_bits, correct_bases)
    data['half_correct_bits'] = randomly_store_half(data['correct_bits'])
    data['confirmed_by_alice'] = confirm_by_alice(alice_bits, data['half_correct_bits'])
    data['outcome'] = create_outcome(data['correct_bits'], data['half_correct_bits'])
    data['eavesdropping_ratio'] = calculate_eavesdropping_ratio(data['confirmed_by_alice'])

    return data

def print_data(data):
    print("\nQUANTUM TRANSMISSION")
    print(f"Alice's random bits:                {data['alice_bits']}")
    print(f"Random sending bases:               {data['alice_bases']}")
    print(f"Random receiving bases:             {data['bob_bases']}")
    print(f"Bits as received by Bob:            {str(data['bob_bits']).replace(',', '')}")
    
    print("\nPUBLIC DISCUSSION")
    print(f"Bob reports used bases:             {data['bob_bases']}")
    print(f"Correct bases according to Alice:   [{' '.join(data['correct_bases'])}]")
    print(f"Presumably shared information:      {str(data['correct_bits']).replace(',', '').replace('-1', ' ')}")
    print(f"Randomly stored half:               {str(data['half_correct_bits']).replace(',', '').replace('-1', ' ')}")
    if data['eve_bases'] is not None:
        print(f"Eve's bases:                        {data['eve_bases']}")
    print(f"Confirmed by Alice:                 [{' '.join(data['confirmed_by_alice'])}]")
    print(f"\nOUTCOME")
    print(f"Remaining shared secret bits:       {str(data['outcome']).replace(',', '').replace('-1', ' ')}")
    print(f"Eavesdropping ratio:                {data['eavesdropping_ratio']:.2f}%")
    if data['eavesdropping_ratio'] > 0:
        print("\nEavesdropping detected!")
    else:
        print("\nChannel is safe!")
    
    print()

def run_tests(num_tests):
    results = {
        "Eavesdropping True": {"detected": 0, "non-detected": 0},
        "Eavesdropping False": {"detected": 0, "non-detected": 0}
    }

    for _ in range(num_tests):
        eavesdropping_enabled = np.random.choice([True, False])
        data = collect_data(eavesdropping_enabled)
        eavesdropping_detected = data['eavesdropping_ratio'] > 0

        if eavesdropping_enabled:
            if eavesdropping_detected:
                results["Eavesdropping True"]["detected"] += 1
            else:
                results["Eavesdropping True"]["non-detected"] += 1
        else:
            if eavesdropping_detected:
                results["Eavesdropping False"]["detected"] += 1
            else:
                results["Eavesdropping False"]["non-detected"] += 1

    print("\nTest Results:")
    print("|                           | Eavesdropping True | Eavesdropping False |")
    print("|---------------------------|--------------------|---------------------|")
    print(f"| Eavesdropping detected    | {results['Eavesdropping True']['detected']:>18} | {results['Eavesdropping False']['detected']:>19} |")
    print(f"| Eavesdropping non-detected| {results['Eavesdropping True']['non-detected']:>18} | {results['Eavesdropping False']['non-detected']:>19} |")

def main():
    eavesdropping_enabled = True
    data = collect_data(eavesdropping_enabled)
    print_data(data)

    num_tests = 100
    run_tests(num_tests)

if __name__ == "__main__":
    main()