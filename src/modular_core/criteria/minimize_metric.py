
class criterion_minimize_measures(cab.criterion_abstract):

    def __init__(self, *args, **kwargs):
        cab.criterion_abstract.__init__(self, *args, **kwargs)
        self.rejects = 1
        self.accepts = 1
        self.reject_probability = 0.5
        self.use_window = False

    def verify_pass(self, *args):
        metrics = args[0]
        #ratio = float(self.accepts)/\
        #   (float(self.accepts) + float(self.rejects))
        #print 'crit accept ratio: ', ratio
        improves = []
        for met in metrics:
            sca = met.data[0].scalars
            if len(sca) <= 100 or not self.use_window:
                improves.append(sca[-1] - min(sca) <=\
                        #   (np.mean(sca) - min(sca)))
                        (np.mean(sca) - min(sca))/25.0)

            else:
                improves.append(sca[-1] - min(sca) <=\
                    (np.mean(sca[-100:]) - min(sca))/20.0)

        weights = [met.acceptance_weight for met in metrics]
        weights = [we/sum(weights) for we, imp in 
                    zip(weights, improves) if imp]
        weight = sum(weights)
        if weight >= self.reject_probability:
        #if improves.count(True) > int(len(improves)/2):
        #if improves.count(True) == len(improves):
            self.accepts += 1
            return True

        self.rejects += 1
        return False
