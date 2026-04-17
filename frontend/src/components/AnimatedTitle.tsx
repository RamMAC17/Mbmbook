export function AnimatedTitle() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="mbm-logo w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden shadow-sm">
        <img src="/logo.png" alt="MBM" className="w-full h-full object-cover rounded-lg" />
      </div>
      <span className="title-text title-glow font-semibold text-sm tracking-wide text-content-primary hidden sm:inline select-none">
        MBM Book
      </span>
    </div>
  )
}
