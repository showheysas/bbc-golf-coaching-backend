import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="flex gap-8">
        <Link 
          href="/player" 
          className="bg-blue-500 text-white py-8 px-12 rounded-lg text-2xl font-bold hover:bg-blue-600 transition-colors duration-200"
        >
          プレイヤー
        </Link>
        
        <Link 
          href="/coach" 
          className="bg-green-500 text-white py-8 px-12 rounded-lg text-2xl font-bold hover:bg-green-600 transition-colors duration-200"
        >
          コーチ
        </Link>
      </div>
    </div>
  )
}